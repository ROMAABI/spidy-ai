from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label, TextArea
from textual.message import Message
from spidy_tui.backend import backend

class SpidyPrompt(Widget):
    """The prompt input component."""
    
    char_count = reactive(0)
    token_estimate = reactive(0)
    wake_word_armed = reactive(backend.wake_word_armed)
    vad_state = reactive(backend.vad_state)

    def watch_wake_word_armed(self, value: bool) -> None:
        self.update_indicators()
        
    def watch_vad_state(self, value: str) -> None:
        self.update_indicators()

    def update_indicators(self) -> None:
        try:
            indicator_label = self.query_one("#voice-indicator", Label)
            if not self.wake_word_armed:
                indicator_label.display = False
            else:
                indicator_label.display = True
                color = "red" if self.vad_state == "listening" else "yellow" if self.vad_state == "processing" else "white"
                indicator_label.update(f"[{color}]🎤 Voice Mode[/]")
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        # Use TextArea for multi-line support, undo/redo, paste etc.
        # Textual's TextArea has built-in undo/redo (Ctrl+Z/Ctrl+Y) and paste support
        with Vertical():
            with Horizontal(id="prompt-header"):
                yield Label("Char: 0 | Tokens: ~0", id="stats-label")
                yield Label("🎤 Voice Mode", id="voice-indicator", classes="hidden")
            
            yield TextArea(language="markdown", id="prompt-input")

    def on_mount(self) -> None:
        self.update_indicators()
        # TextArea starts in dark theme by default but we control via CSS mostly
        self.query_one(TextArea).focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        self.char_count = len(text)
        self.token_estimate = int(self.char_count / 4.0)
        
        try:
            self.query_one("#stats-label", Label).update(f"Char: {self.char_count} | Tokens: ~{self.token_estimate}")
        except Exception:
            pass
            
        # Check for command palette trigger
        if text.endswith("/") and not text.strip() == "":
            pass # App will handle this via key event
            
    async def on_key(self, event) -> None:
        text_area = self.query_one(TextArea)
        if event.key == "enter":
            event.prevent_default()
            text = text_area.text.strip()
            if text:
                self.post_message(self.Submitted(text))
                text_area.text = ""
        elif event.key == "shift+enter":
            # Let TextArea handle newline
            pass
            
    class Submitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()
