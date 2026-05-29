from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
import subprocess
import time
import asyncio
from spidy_tui.backend import backend

class SpidyFooter(Widget):
    """Cyberpunk footer bar matching the mockup exactly."""
    
    branch = reactive("main")
    latency = reactive(42)
    
    def on_mount(self) -> None:
        self.branch = self.get_git_branch()
        self.latency_task = asyncio.create_task(self.measure_latency_loop())
        self.update_footer()
        
    def get_git_branch(self) -> str:
        try:
            res = subprocess.check_output(
                ["git", "branch", "--show-current"], 
                stderr=subprocess.DEVNULL
            )
            return res.decode().strip() or "main"
        except Exception:
            return "main"
            
    async def measure_latency_loop(self) -> None:
        while True:
            try:
                start = time.perf_counter()
                ok = await backend.check_connection()
                elapsed = (time.perf_counter() - start) * 1000
                self.latency = int(elapsed) if ok else 999
                self.update_footer()
            except Exception:
                pass
            await asyncio.sleep(5.0)
            
    def update_footer(self) -> None:
        try:
            left_label = self.query_one("#footer-left-label", Label)
            right_label = self.query_one("#footer-right-label", Label)
            
            left_label.update(
                f"[red]WS:[/red] spidy-ai   |   [red]BRANCH:[/red] {self.branch}"
            )
            
            # Format latency color based on quality
            lat_color = "cyan" if self.latency < 100 else ("yellow" if self.latency < 300 else "red")
            right_label.update(
                f"📡 LATENCY: [{lat_color}]{self.latency}ms[/{lat_color}]   |   "
                f"OUTPUT: [cyan]Normal[/cyan]   |   "
                f"MODE: [cyan]Active[/cyan]"
            )
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("", id="footer-left-label", classes="footer-left")
            yield Label("", id="footer-right-label", classes="footer-right")
            
    def on_unmount(self) -> None:
        try:
            self.latency_task.cancel()
        except Exception:
            pass
