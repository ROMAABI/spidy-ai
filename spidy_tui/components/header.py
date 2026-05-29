from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
import time
import psutil
import asyncio
from datetime import datetime
from spidy_tui.backend import backend

class SpidyHeader(Widget):
    """Cyberpunk header component matching the mockup exactly."""
    
    cpu_val = reactive(17)
    mem_val = reactive(84)
    task_count = reactive(2)
    time_str = reactive("08:15:42 AM")
    
    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_stats)
        self.update_stats()
        
    def update_stats(self) -> None:
        # Get actual CPU and Memory usage
        try:
            self.cpu_val = int(psutil.cpu_percent())
            self.mem_val = int(psutil.virtual_memory().percent)
        except Exception:
            pass
            
        # Get count of active tasks in the event loop as a dynamic indicator
        try:
            self.task_count = len([t for t in asyncio.all_tasks() if not t.done()])
        except Exception:
            self.task_count = 2
            
        # Format current time
        self.time_str = datetime.now().strftime("%I:%M:%S %p")
        
        # Update UI labels
        try:
            self.query_one("#header-center-label", Label).update(
                f"[red]• STATUS: LISTENING[/red]   "
                f"MODEL: [cyan]{backend.model_name}[/cyan]   "
                f"MEM: [cyan]{self.mem_val}%[/cyan]   "
                f"CPU: [cyan]{self.cpu_val}%[/cyan]   "
                f"TASKS: [cyan]{self.task_count}[/cyan]"
            )
            self.query_one("#header-right-label", Label).update(
                f"{self.time_str}  ⚙ 🗄 ☰"
            )
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("🕸  SPIDY_v1.0", classes="header-left")
            yield Label("", id="header-center-label", classes="header-center")
            yield Label("", id="header-right-label", classes="header-right")
