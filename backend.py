"""
WARNING: This is a DEPRECATED mock backend.

The REAL backend lives at spidy_tui/backend.py.

All imports have been migrated to:
    from spidy_tui.backend import BackendManager, backend

This file is kept only as a reference. It will be removed in a future cleanup.
To use the real backend, delete this file — nothing imports it anymore.
"""
import asyncio
import random
from typing import AsyncGenerator, Dict, Any, Callable

# Mock data
MOCK_SKILLS = [
    "weather", "file_ops", "system_control", "web_search",
    "time", "calculator", "browser", "calendar",
    "notes", "email", "music", "lights"
]


class BackendManager:
    """
    DEPRECATED — use spidy_tui.backend.BackendManager instead.
    """
    def __init__(self):
        self.vad_state = "idle"
        self.wake_word_armed = False
        self.tts_enabled = True
        self.model_name = "kimi-k2"
        self.provider_name = "ollama"
        self.token_speed = 45.2
        self.ollama_connected = True

        self.memory_stats = {
            "ram_usage_mb": 450,
            "chromadb_vectors": 1245,
            "sqlite_rows": 834
        }

        self.active_skills = {skill: False for skill in MOCK_SKILLS}
        self.on_vad_state_change: Callable[[str], None] = lambda state: None
        self.on_wake_word_state_change: Callable[[bool], None] = lambda state: None

    async def toggle_wake_word(self):
        self.wake_word_armed = not self.wake_word_armed
        self.on_wake_word_state_change(self.wake_word_armed)

        if self.wake_word_armed:
            self.bg_task = asyncio.create_task(self._simulate_voice_interaction())

    async def _simulate_voice_interaction(self):
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

        self.vad_state = "idle"
        self.on_vad_state_change(self.vad_state)

    async def stream_chat_response(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        # Simulate thinking
        yield {"type": "thinking_start"}
        await asyncio.sleep(0.5)
        yield {"type": "thinking_token", "content": "I "}
        await asyncio.sleep(0.1)
        yield {"type": "thinking_token", "content": "need "}
        await asyncio.sleep(0.1)
        yield {"type": "thinking_token", "content": "to "}
        await asyncio.sleep(0.1)
        yield {"type": "thinking_token", "content": "think "}
        await asyncio.sleep(0.1)
        yield {"type": "thinking_token", "content": "about "}
        await asyncio.sleep(0.1)
        yield {"type": "thinking_end"}

        # Simulate streaming response
        response_words = [
            "Hello", "! ", "I'm ", "a ", "mock ", "backend", ". ",
            "This ", "is ", "fake ", "streaming", "."
        ]
        for word in response_words:
            yield {"type": "token", "content": word}
            await asyncio.sleep(0.05)

    def clear_conversation(self) -> None:
        pass
