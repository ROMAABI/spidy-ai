from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
import time
from spidy_tui.backend import backend

class SpidyHeader(Widget):
    """The header component."""
    
    session_name = reactive("New Session")
    model_name = reactive(backend.model_name)
    provider_name = reactive(backend.provider_name)
    token_count = reactive(0)
    uptime = reactive(0)
    
    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_uptime)
        self._start_time = time.time()
        
    def update_uptime(self) -> None:
        self.uptime = int(time.time() - self._start_time)

    def watch_session_name(self, value: str) -> None:
        try:
            self.query_one("#header-center-label", Label).update(f"{self.session_name} · {self.model_name} ({self.provider_name})")
        except Exception:
            pass

    def watch_model_name(self, value: str) -> None:
        try:
            self.query_one("#header-center-label", Label).update(f"{self.session_name} · {self.model_name} ({self.provider_name})")
        except Exception:
            pass

    def watch_token_count(self, value: int) -> None:
        try:
            self.query_one("#header-right-label", Label).update(self._format_right())
        except Exception:
            pass
        
    def watch_uptime(self, value: int) -> None:
        try:
            self.query_one("#header-right-label", Label).update(self._format_right())
        except Exception:
            pass
        
    def _format_right(self) -> str:
        mins, secs = divmod(self.uptime, 60)
        hours, mins = divmod(mins, 60)
        time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{self.token_count} ctx · {time_str}"

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("🕸 SPIDY AI", classes="header-left")
            yield Label(f"{self.session_name} · {self.model_name} ({self.provider_name})", id="header-center-label", classes="header-center")
            yield Label(self._format_right(), id="header-right-label", classes="header-right")
