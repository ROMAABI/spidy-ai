import re
import time
import threading
import asyncio
import yaml
from core.tts import TTS
from core.brain import Brain
from core.memory import Memory
from tools.executor import Executor

# ── Command framework ─────────────────────────────────────────────────────
from spidy.commands.parser import parse as parse_cmd, ParsedMessage
from spidy.commands import CommandRegistry
from spidy.shell import ShellExecutor
from spidy.fileref import resolve_file_refs, inject_file_context
from spidy.agents import get_mode

# Load all slash command modules (they self-register via CommandRegistry.register())
try:
    import spidy.commands.__loader__  # noqa: F401
except Exception:
    pass

from skills import ALL_SKILLS
from skills.apps import AppsSkill
from skills.sysinfo import SysinfoSkill
from skills.media import MediaSkill
from skills.search import SearchSkill
from skills.messaging import MessagingSkill
from skills.code_executor import CodeExecutorSkill
from skills.alarm import AlarmSkill
from skills.clipboard import ClipboardSkill
from skills.hyprland import HyprlandSkill

with open("config.yaml") as f:
    config = yaml.safe_load(f)


class Assistant:
    def _log(self, msg: str):
        print(f"[Spidy] {msg}")

    def __init__(self, ui=None, show_thinking: bool = False):
        self.ui = ui
        self.mode = "voice"
        self.lang = "en"
        self._processing = False
        self.active_mode = None

        self._log("Initializing Spidy...")

        self._stt = None
        self.tts = TTS()
        self.brain = Brain(show_thinking=show_thinking)
        self.memory = Memory()

        self.executor = Executor(on_speak=self._speak, on_status=self._set_status)

        self.alarm_skill = AlarmSkill()
        self.alarm_skill.set_speaker(self.tts.speak)

        self.skills = [
            HyprlandSkill(),
            *[cls() for cls in ALL_SKILLS],
            AppsSkill(),
            SysinfoSkill(),
            MediaSkill(),
            SearchSkill(),
            MessagingSkill(),
            CodeExecutorSkill(),
            self.alarm_skill,
            ClipboardSkill(),
        ]

        self._log("Spidy ready!")

    @property
    def stt(self):
        if self._stt is None:
            from core.stt import STT
            self._stt = STT()
        return self._stt

    def set_ui(self, ui):
        self.ui = ui

    def set_mode(self, mode: str):
        self.mode = mode
        self._log(f"Mode switched to {mode}")

    async def _handle_command_async(self, parsed: ParsedMessage) -> str | None:
        if parsed.type == "slash":
            result = await CommandRegistry.dispatch(
                parsed.command, parsed.args, {"assistant": self}
            )
            return result.output
        if parsed.type == "mode":
            mode = get_mode(parsed.mode)
            if mode:
                self.active_mode = mode
                return f"Switched to @{mode.name} mode: {mode.description}"
            return f"Unknown mode: @{parsed.mode}. Try: plan, build, general, system, research"
        if parsed.type == "shell":
            executor = ShellExecutor(timeout=15)
            result = await executor.run(parsed.shell_cmd)
            output = result.output
            if len(output) > 2000:
                output = output[:2000] + "\n... [truncated]"
            return f"$ {parsed.shell_cmd}\n{output}"
        return None

    def _handle_command(self, parsed: ParsedMessage) -> str | None:
        try:
            return asyncio.run(self._handle_command_async(parsed))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._handle_command_async(parsed))
            finally:
                loop.close()
        except Exception as e:
            return f"Command error: {e}"

    def process(self, text: str):
        if not text.strip():
            return

        self.lang = self._detect_lang(text)

        # ── Parse input for commands / modes / shell / file refs ────────
        parsed = parse_cmd(text)
        cmd_response = self._handle_command(parsed)

        if cmd_response is not None:
            self._add_message("user", text)
            self._set_status("listening")
            # If there are file refs with the command, show them
            file_context = inject_file_context(resolve_file_refs(parsed.filerefs))
            response = cmd_response + file_context if file_context else cmd_response
            self._add_message("spidy", response)
            print(f"\n{response}")
            return

        self._add_message("user", text)
        self._set_status("thinking")

        if self.executor.has_pending():
            self.executor.confirm(text)
            return

        exit_words = ["bye", "tata", "poidu", "exit", "quit"]
        if any(w in text.lower() for w in exit_words):
            self._speak(
                "Bye anna, pakkalam!" if self.lang == "ta" else "Goodbye! See you soon."
            )
            return

        # Try instant keyword action (bypasses LLM)
        from core.actions import match_action, execute_action
        action_cmd = match_action(text)
        if action_cmd:
            result = execute_action(action_cmd)
            if result["success"]:
                msg = f"Done! {result['output']}" if result["output"] else "Done!"
            else:
                msg = f"Failed: {result['output']}"
            self._add_message("spidy", msg)
            self._speak(msg)
            self._set_status("listening")
            return

        # ── Inject file references into chat context ────────────────────
        if parsed.filerefs:
            file_ctx = inject_file_context(resolve_file_refs(parsed.filerefs))
            text = text + file_ctx

        skill_result = self._try_skill(text)
        if skill_result:
            msg = skill_result.get(
                f"speak_{self.lang}", skill_result.get("speak_en", "Done!")
            )
            if skill_result.get("needs_confirm") and skill_result.get("command"):
                self.executor.execute(skill_result["command"])
                return
            self._add_message("spidy", msg)
            self._speak(msg)
            self._set_status("listening")
            return

        self._ask_brain(text)

    def _process_and_release(self, text: str):
        try:
            self.process(text)
        except Exception as e:
            self._log(f"Process error: {e}")
        finally:
            time.sleep(1.0)
            self._processing = False
            self._log("Ready to listen again...")

    def _try_skill(self, text: str):
        for skill in self.skills:
            if skill.can_handle(text):
                result = skill.run(text, lang=self.lang)
                if result.get("command"):
                    self.executor.execute(result["command"])
                return result
        return None

    def _ask_brain(self, text: str):
        history = self.memory.get_history()
        self.memory.add("user", text)

        sentence_buffer = ""
        full_response = ""
        spoken_sentences = set()

        def on_token(token: str):
            nonlocal sentence_buffer, full_response
            sentence_buffer += token
            full_response += token

            if self.ui and hasattr(self.ui, "signals"):
                try:
                    self.ui.signals.set_stream.emit(
                        self._clean_for_display(full_response)
                    )
                except Exception:
                    pass

            if any(p in token for p in [".", "!", "?", "\n"]):
                sentence = sentence_buffer.strip()
                sentence_buffer = ""
                if self.mode == "text":
                    print(sentence, end=" ", flush=True)
                else:
                    clean_sentence = self._clean_for_speech(sentence)
                    if clean_sentence and clean_sentence not in spoken_sentences:
                        spoken_sentences.add(clean_sentence)
                        self.tts.speak(clean_sentence, self.lang)

        self._set_status("thinking")
        full_response = self.brain.chat(history, on_token=on_token)

        if sentence_buffer.strip():
            if self.mode == "text":
                print(sentence_buffer.strip(), flush=True)
            else:
                clean = self._clean_for_speech(sentence_buffer.strip())
                if clean and clean not in spoken_sentences:
                    self.tts.speak(clean, self.lang)

        bash_blocks = re.findall(r"```bash\n(.*?)\n```", full_response, flags=re.DOTALL)
        for cmd in bash_blocks:
            self.executor.execute(cmd.strip())

        self.memory.add("assistant", full_response)

        if self.ui and hasattr(self.ui, "signals"):
            try:
                self.ui.signals.set_stream.emit("")
            except Exception:
                pass

        clean = self._clean_for_display(full_response)
        if clean:
            self._add_message("spidy", clean)

        self._set_status("listening")

    def voice_loop(self):
        import random
        from datetime import datetime

        greetings_en = [
            "Hey Abi, Spidy is ready! What can I do for you?",
            "Hello anna, I am all ears!",
            "Spidy online! How can I help you today?",
            "Good to see you anna! What do you need?",
            "Hey! Spidy here, ready to assist!",
            "What's up anna! Spidy is ready!",
            "I am awake anna! What do you need?",
        ]
        greetings_ta = [
            "\u0b8f\u0baf\u0bcd \u0b85\u0baa\u0bbf, \u0bb8\u0bcd\u0baa\u0bc8\u0b9f\u0bbf \u0ba4\u0baf\u0bbe\u0bb0\u0bcd! \u0b89\u0ba9\u0b95\u0bcd\u0b95\u0bc1 \u0b8e\u0ba9\u0bcd\u0ba9 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bb2\u0bbe\u0bae\u0bcd?",
            "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd \u0b85\u0ba3\u0bcd\u0ba3\u0bbe, \u0ba8\u0bbe\u0ba9\u0bcd \u0b95\u0bc7\u0b9f\u0bcd\u0b9f\u0bc1\u0b95\u0bcd\u0b95\u0bca\u0ba3\u0bcd\u0b9f\u0bbf\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0bb1\u0bc7\u0ba9\u0bcd!",
            "\u0bb8\u0bcd\u0baa\u0bc8\u0b9f\u0bbf \u0b86\u0ba9\u0bcd\u0bb2\u0bc8\u0ba9\u0bcd! \u0b8e\u0baa\u0bcd\u0baa\u0b9f\u0bbf \u0b89\u0ba4\u0bb5\u0bb2\u0bbe\u0bae\u0bcd?",
            "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bc8 \u0baa\u0bbe\u0bb0\u0bcd\u0ba4\u0bcd\u0ba4\u0ba4\u0bbf\u0bb2\u0bcd \u0bae\u0b95\u0bbf\u0bb4\u0bcd\u0b9a\u0bcd\u0b9a\u0bbf \u0b85\u0ba3\u0bcd\u0ba3\u0bbe! \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0b8e\u0ba9\u0bcd\u0ba9 \u0bb5\u0bc7\u0ba3\u0bc1\u0bae\u0bcd?",
        ]

        greet_list = greetings_ta if self.lang == "ta" else greetings_en
        greeting = random.choice(greet_list)
        self._speak(greeting)

        while True:
            try:
                text, lang = self.stt.listen()
                if text.strip():
                    self.lang = lang if lang else self.lang
                    self._log(f"You ({lang}): {text}")
                    self.process(text)
            except KeyboardInterrupt:
                self._log("Exiting voice loop...")
                break
            except Exception as e:
                self._log(f"Voice loop error: {e}")
                time.sleep(1)

    def start(self):
        if self.mode == "voice":
            thread = threading.Thread(target=self.voice_loop, daemon=True)
            thread.start()
            thread.join()
        else:
            self._log("Text mode: type your message below (type 'exit' to quit)")
            self._log("=" * 50)
            while True:
                try:
                    text = input("> ").strip()
                    if not text:
                        continue
                    if text.lower() in ("exit", "quit", "bye"):
                        self._speak("Goodbye!")
                        break
                    self.process(text)
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

    def _speak(self, text: str):
        clean = self._clean_for_speech(text)
        if self.mode == "text":
            print(f"[Spidy] {clean}")
        else:
            self.tts.speak(clean, self.lang)

    def _detect_lang(self, text: str) -> str:
        tamil_chars = re.findall(r"[\u0B80-\u0BFF]", text)
        return "ta" if len(tamil_chars) > 2 else "en"

    def _set_status(self, status: str):
        if self.ui and hasattr(self.ui, "signals"):
            try:
                self.ui.signals.set_status.emit(status)
            except Exception:
                pass

    def _add_message(self, role: str, text: str):
        if self.ui and hasattr(self.ui, "signals"):
            try:
                self.ui.signals.add_message.emit(role, text)
            except Exception:
                pass

    def _clean_for_speech(self, text: str) -> str:
        clean = re.sub(r"\*+", "", text)
        clean = re.sub(r"```[\s\S]*?```", "", clean)
        clean = re.sub(r"\[.*?\]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _clean_for_display(self, text: str) -> str:
        clean = re.sub(r"\*+", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean