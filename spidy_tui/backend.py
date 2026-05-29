"""
spidy_tui/backend.py — Real Ollama streaming backend
Fixes:
   1. Replaced mock stream with real ollama.AsyncClient streaming
   2. token_speed now measured live (not hardcoded 45.2)
   3. on_vad_state_change / on_wake_word_state_change callbacks
      now thread-safe via call_from_thread
   4. stream_chat_response yields message_end reliably
   5. System prompt is now injected from spidy.system_prompt (single source of truth)
   6. Intent router intercepts executable commands (open, screenshot, system stats, etc.)
      BEFORE sending to LLM — prevents generic chatbot responses
"""
import asyncio
import os
import time
import re
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Callable

import ollama
from openai import AsyncOpenAI
from spidy.system_prompt import build_system_prompt
from core.actions import match_action, execute_action
from core.permissions import classify_command, log_permission, get_permission_prompt, get_voice_prompt, validate_confirmation
from core.tts import (
    TTS,
    cancel_speech,
    clean_text,
    split_sentences,
    is_speaking,
    get_queue_size,
    get_last_latency_ms,
    get_tts_status,
    get_tts_engine,
)
from skills.system.app_control import _classify_intent

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Lazy-import skills to avoid circular imports
_INTENT_SKILLS: list | None = None

def _load_intent_skills() -> list:
    """Build the same skill list as Assistant._try_skill uses."""
    global _INTENT_SKILLS
    if _INTENT_SKILLS is not None:
        return _INTENT_SKILLS
    skills = []
    try:
        from skills import ALL_SKILLS
        skills = [cls() for cls in ALL_SKILLS]
    except Exception:
        pass
    # Add standalone skills that Assistant also loads
    for mod_name, cls_name in [
        ("skills.apps", "AppsSkill"),
        ("skills.sysinfo", "SysinfoSkill"),
        ("skills.media", "MediaSkill"),
        ("skills.search", "SearchSkill"),
        ("skills.messaging", "MessagingSkill"),
        ("skills.code_executor", "CodeExecutorSkill"),
        ("skills.clipboard", "ClipboardSkill"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            skills.append(cls())
        except Exception:
            continue
    _INTENT_SKILLS = skills
    return skills


class BackendManager:
    def __init__(self):
        self.vad_state = "idle"
        self.wake_word_armed = False
        self.tts_enabled = True
        self._tts = self._init_tts()

        self.provider_name = "openrouter"
        self.model_name = "deepseek/deepseek-chat-v3-0324"
        self._fallback_provider = "ollama"
        self._fallback_model = "gemma4:e2b"
        self._openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        self._openrouter_url = "https://openrouter.ai/api/v1"
        self._openai_client: AsyncOpenAI | None = None

        self._system_prompt = build_system_prompt(Path("config.yaml"))
        self.token_speed: float = 0.0
        self.ollama_connected = False
        self._conversation: list[dict[str, str]] = []

        self.memory_stats: dict = {}
        self.active_skills: list = []
        self._pending_permission: dict | None = None
        self._pending_steps: list[str] = []
        self._step_delay: float = 2.0
        self._permission_timeout: float = 60.0

        self.on_vad_state_change: Callable[[str], None] = lambda _: None
        self.on_wake_word_state_change: Callable[[bool], None] = lambda _: None
        self.on_token_speed_change: Callable[[float], None] = lambda _: None

        self._intent_skills: list = _load_intent_skills()
        self._bg_task: asyncio.Task | None = None

        # Streaming TTS sentence boundary pattern
        self._sentence_end_re = re.compile(r"(?<=[.!?])\s+(?=[\"'(]?[A-Z0-9])")
        self._tts_max_chunk = 300
        self._tts_min_chunk = 15

    @staticmethod
    def _init_tts():
        """Lazy-init TTS engine (may fail if audio deps missing)."""
        try:
            from core.tts import TTS
            return TTS()
        except Exception:
            return None

    def _get_openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(
                api_key=self._openrouter_key,
                base_url=self._openrouter_url,
            )
        return self._openai_client

    async def check_connection(self) -> bool:
        try:
            if self.provider_name == "openrouter":
                client = self._get_openai_client()
                await client.models.list()
            else:
                client = ollama.AsyncClient()
                await client.list()
            self.ollama_connected = True
        except Exception:
            self.ollama_connected = False
        return self.ollama_connected

    # ── Intent router (pre-LLM) ────────────────────────────────────────

    def _parse_multi_step(self, text: str) -> list[str]:
        text_lower = text.lower().strip()
        if " and " not in text_lower:
            return [text]
        parts = text.split(" and ")
        steps = []
        for part in parts:
            part = part.strip()
            if part:
                steps.append(part)
        return steps if len(steps) > 1 else [text]

    def _try_intent(self, text: str) -> str | None:
        if self._pending_permission:
            elapsed = time.time() - self._pending_permission.get("timestamp", 0)
            if elapsed > self._permission_timeout:
                self._pending_permission = None
                return "Permission request expired. Please try again."
            text_lower = text.strip().lower()
            if text_lower in ("yes", "y", "confirm", "proceed", "do it",
                              "no", "n", "cancel", "deny", "stop"):
                return self.confirm_permission(text)

        intent, confidence = _classify_intent(text)

        if intent == "QUESTION":
            return None
        if intent == "CHAT":
            return None

        if intent == "SEARCH":
            for skill in self._intent_skills:
                if skill.name == "search" and skill.can_handle(text):
                    result = skill.run(text, lang="en")
                    if result.get("success"):
                        return result.get("speak_en", "Done.")
                    return None
            return None

        if intent == "COMMAND" and confidence >= 0.90:
            steps = self._parse_multi_step(text)
            if len(steps) > 1:
                self._pending_steps = steps[1:]
                self._step_delay = 2.0
                text = steps[0]
                intent, confidence = _classify_intent(text)

            try:
                action_cmd = match_action(text)
                if action_cmd:
                    perm_req = classify_command(action_cmd)
                    if perm_req:
                        log_permission(action_cmd, False, "permission_required_pending")
                        prompt = get_permission_prompt(perm_req)
                        self._pending_permission = {
                            "command": action_cmd,
                            "request": perm_req,
                            "timestamp": time.time(),
                        }
                        return f"[PERMISSION_REQUIRED]\n{prompt}"
                    result = execute_action(action_cmd)
                    if result["success"]:
                        return result["output"] or "Done!"
                    return f"Failed: {result['output']}"
            except Exception:
                pass

            for skill in self._intent_skills:
                try:
                    if skill.can_handle(text):
                        result = skill.run(text, lang="en")
                        cmd = result.get("command")
                        if cmd:
                            perm_req = classify_command(cmd)
                            if perm_req:
                                log_permission(cmd, False, "permission_required_pending")
                                prompt = get_permission_prompt(perm_req)
                                self._pending_permission = {
                                    "command": cmd,
                                    "request": perm_req,
                                    "timestamp": time.time(),
                                }
                                return f"[PERMISSION_REQUIRED]\n{prompt}"
                            execute_action(cmd)
                        msg = result.get("speak_en", "Done!")
                        if result.get("success", True):
                            return msg
                        return f"Failed: {msg}"
                except Exception:
                    continue

        return None

    def confirm_permission(self, confirmation: str) -> str | None:
        if not self._pending_permission:
            return None
        cmd = self._pending_permission["command"]
        req = self._pending_permission["request"]
        self._pending_permission = None
        if validate_confirmation(confirmation, req):
            log_permission(cmd, True, "user_confirmed")
            result = execute_action(cmd, permission_granted=True)
            output = result["output"] if result["success"] else f"Failed: {result['output']}"
            if self._pending_steps:
                remaining = self._pending_steps
                self._pending_steps = []
                for step in remaining:
                    time.sleep(self._step_delay)
                    step_result = self._execute_single(step)
                    output += f"\n{step_result}"
            return output or "Done!"
        log_permission(cmd, False, "user_denied")
        self._pending_steps = []
        return "Command cancelled."

    def _execute_single(self, text: str) -> str:
        intent, confidence = _classify_intent(text)
        if intent != "COMMAND":
            return f"Skipped: {text}"
        try:
            action_cmd = match_action(text)
            if action_cmd:
                perm_req = classify_command(action_cmd)
                if perm_req:
                    return f"Needs permission: {action_cmd}"
                result = execute_action(action_cmd)
                return result["output"] if result["success"] else f"Failed: {result['output']}"
        except Exception:
            pass
        for skill in self._intent_skills:
            try:
                if skill.can_handle(text):
                    result = skill.run(text, lang="en")
                    cmd = result.get("command")
                    if cmd:
                        perm_req = classify_command(cmd)
                        if perm_req:
                            return f"Needs permission: {cmd}"
                        execute_action(cmd)
                    return result.get("speak_en", "Done!")
            except Exception:
                continue
        return f"Could not execute: {text}"

    # ── Streaming TTS sentence flushing ───────────────────────────────

    def _flush_tts_chunks(self, buffer: str, generation: int) -> str:
        """Feed complete sentences from *buffer* to the TTS engine.

        Returns the remaining (possibly partial) text after the last
        sentence boundary.  Also force-flushes when the buffer exceeds
        ``_tts_max_chunk`` characters.
        """
        if not buffer or not self._tts:
            return buffer

        parts = self._sentence_end_re.split(buffer)
        # If the split produced only one part, no complete sentence yet
        if len(parts) <= 1:
            # Force-flush if buffer is too long (prevent starvation)
            if len(buffer) >= self._tts_max_chunk:
                cleaned = clean_text(buffer.strip())
                if cleaned:
                    print(f"[TTS] Streaming force-flush ({len(buffer)} chars): \"{cleaned[:60]}...\"")
                    self._tts.feed_chunk(cleaned, generation)
                return ""
            return buffer

        # All parts except the last are complete sentences
        for part in parts[:-1]:
            cleaned = clean_text(part.strip())
            if cleaned and len(cleaned) >= self._tts_min_chunk:
                print(f"[TTS] Streaming sentence: \"{cleaned[:60]}...\" ({len(cleaned)} chars)")
                self._tts.feed_chunk(cleaned, generation)

        return parts[-1].strip() if parts[-1].strip() else ""

    # ── Core streaming ─────────────────────────────────────────────────

    async def stream_chat_response(
        self, prompt: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        cancel_speech()
        t_user = time.perf_counter()
        print(f"[TTS-TIME] User message received: {t_user:.3f}")

        intent_result = self._try_intent(prompt)
        if intent_result is not None:
            yield {"type": "message_start"}
            yield {"type": "message_token", "content": intent_result}
            yield {"type": "message_end"}
            # Speak command result via streaming TTS
            if self.tts_enabled and self._tts and intent_result.strip():
                gen = self._tts.new_generation()
                chunks = split_sentences(intent_result)
                for chunk in chunks:
                    cleaned = clean_text(chunk)
                    if cleaned:
                        self._tts.feed_chunk(cleaned, gen)
                self._tts.finish_generation(gen)
            return

        self._conversation.append({"role": "user", "content": prompt})

        yield {"type": "message_start"}

        token_count = 0
        t_start = time.perf_counter()
        print(f"[TTS-TIME] LLM response started: {t_start:.3f}")
        accumulated = []

        # ── Streaming TTS state ────────────────────────────────────────
        _tts_ref = self._tts
        tts_gen: int | None = None
        if self.tts_enabled and _tts_ref is not None:
            tts_gen = _tts_ref.new_generation()
        tts_sentence_buffer = ""
        tts_first_chunk_sent = False
        t_tts_chunk_start: float | None = None

        messages = [
            {"role": "system", "content": self._system_prompt},
            *self._conversation,
        ]

        try:
            if self.provider_name == "openrouter":
                try:
                    async for token in self._stream_openrouter(messages):
                        accumulated.append(token)
                        token_count += 1
                        yield {"type": "message_token", "content": token}

                        # ── Streaming TTS: buffer and flush sentences ──
                        if tts_gen is not None:
                            tts_sentence_buffer = self._flush_tts_chunks(
                                tts_sentence_buffer + token,
                                tts_gen,
                            )
                except Exception as or_err:
                    print(f"[TUI] OpenRouter failed ({or_err}), falling back to Ollama")
                    async for token in self._stream_ollama(messages):
                        accumulated.append(token)
                        token_count += 1
                        yield {"type": "message_token", "content": token}

                        if tts_gen is not None:
                            tts_sentence_buffer = self._flush_tts_chunks(
                                tts_sentence_buffer + token,
                                tts_gen,
                            )
            else:
                async for token in self._stream_ollama(messages):
                    accumulated.append(token)
                    token_count += 1
                    yield {"type": "message_token", "content": token}

                    if tts_gen is not None:
                        tts_sentence_buffer = self._flush_tts_chunks(
                            tts_sentence_buffer + token,
                            tts_gen,
                        )

            t_done = time.perf_counter()
            print(f"[TTS-TIME] LLM response completed: {t_done:.3f} ({t_done - t_start:.2f}s)")

            elapsed = t_done - t_start
            if elapsed > 0 and token_count > 0:
                self.token_speed = round(token_count / elapsed, 1)
                self.on_token_speed_change(self.token_speed)

            full_reply = "".join(accumulated)
            self._conversation.append(
                {"role": "assistant", "content": full_reply}
            )
            self.ollama_connected = True

            # ── Flush any remaining TTS buffer ─────────────────────────
            if tts_gen is not None and tts_sentence_buffer.strip():
                cleaned = clean_text(tts_sentence_buffer.strip())
                if cleaned:
                    if not tts_first_chunk_sent:
                        t_tts_chunk_start = time.perf_counter()
                        print(f"[TTS-TIME] First TTS chunk sent: {t_tts_chunk_start:.3f}")
                        tts_first_chunk_sent = True
                    print(f"[TTS] Streaming last-chunk: \"{cleaned[:60]}...\" ({len(cleaned)} chars)")
                    if _tts_ref is not None:
                        _tts_ref.feed_chunk(cleaned, tts_gen)

            if tts_gen is not None and _tts_ref is not None:
                _tts_ref.finish_generation(tts_gen)
                if tts_first_chunk_sent and t_tts_chunk_start:
                    t_last = time.perf_counter()
                    print(f"[TTS-TIME] All streaming chunks dispatched: {t_last:.3f} "
                          f"(latency to first chunk: {(t_tts_chunk_start - t_start)*1000:.0f}ms)")

        except Exception as exc:
            self.ollama_connected = False
            yield {"type": "error", "content": str(exc)}

        finally:
            yield {"type": "message_end"}

    def clear_conversation(self) -> None:
        self._conversation.clear()

    async def _stream_openrouter(self, messages: list[dict[str, str]]):
        client = self._get_openai_client()
        stream = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            max_tokens=4096,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def _stream_ollama(self, messages: list[dict[str, str]]):
        client = ollama.AsyncClient()
        async for part in await client.chat(
            model=self._fallback_model,
            messages=messages,
            stream=True,
        ):
            token = part["message"]["content"]
            if token:
                yield token

    # ── Wake word / VAD (unchanged logic, cleaner) ─────────────────────

    async def toggle_wake_word(self) -> None:
        self.wake_word_armed = not self.wake_word_armed
        self.on_wake_word_state_change(self.wake_word_armed)

        if self.wake_word_armed:
            self._bg_task = asyncio.create_task(
                self._simulate_voice_interaction()
            )
        elif self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()

    async def _simulate_voice_interaction(self) -> None:
        """Placeholder — replace with real faster-whisper VAD loop."""
        try:
            await asyncio.sleep(5)
            if not self.wake_word_armed:
                return

            self.vad_state = "listening"
            self.on_vad_state_change(self.vad_state)
            await asyncio.sleep(3)

            if not self.wake_word_armed:
                self.vad_state = "idle"
                self.on_vad_state_change(self.vad_state)
                return

            self.vad_state = "processing"
            self.on_vad_state_change(self.vad_state)
            await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        finally:
            self.vad_state = "idle"
            self.on_vad_state_change(self.vad_state)


backend = BackendManager()
