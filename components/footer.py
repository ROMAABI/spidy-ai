from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from spidy_tui.backend import backend

class SpidyFooter(Widget):
    """The footer component."""
    
    connected = reactive(backend.ollama_connected)
    tts_enabled = reactive(backend.tts_enabled)
    
    def watch_connected(self, value: bool) -> None:
        self.update_right()
        
    def watch_tts_enabled(self, value: bool) -> None:
        self.update_right()

    def update_right(self) -> None:
        status_dot = "🟢" if self.connected else "🔴"
        tts_status = "🔊 TTS: ON" if self.tts_enabled else "🔇 TTS: OFF"
        try:
            self.query_one("#footer-right-label", Label).update(f"{status_dot} Ollama  |  {tts_status}")
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("[Ctrl+C] Exit  \\[/] Commands  [Tab] Agent  [F1] Help", classes="footer-left")
            status_dot = "🟢" if self.connected else "🔴"
            tts_status = "🔊 TTS: ON" if self.tts_enabled else "🔇 TTS: OFF"
            yield Label(f"{status_dot} Ollama  |  {tts_status}", id="footer-right-label", classes="footer-right")
