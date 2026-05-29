"""Dashboard-style sidebar displaying real-time developer context."""

import os
import shutil
import subprocess
import time
from datetime import datetime, timezone

import psutil

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from spidy_tui.backend import backend
from core.tts import (
    get_queue_size,
    get_last_latency_ms,
    get_tts_engine,
    get_tts_status,
    get_volume,
    is_speaking,
)


def make_sparkline(history: list[int]) -> str:
    chars = " ▂▃▄▅▆▇█"
    spark = ""
    for val in history:
        idx = min(7, max(0, int(val * 8 / 100)))
        spark += chars[idx]
    return spark


class SpidySidebar(Widget):
    """Dashboard-style sidebar with real-time developer and AI context."""

    # System stats
    cpu_history = reactive(lambda: [0] * 6)
    mem_history = reactive(lambda: [0] * 6)
    disk_history = reactive(lambda: [0] * 6)
    uptime_str = reactive("0m")

    # Git stats
    git_branch = reactive("")
    git_uncommitted = reactive(0)
    git_last_commit = reactive("")

    # TTS live stats (polled)
    tts_status = reactive("idle")
    tts_queue = reactive(0)
    tts_latency = reactive(0)
    tts_volume = reactive(100)
    tts_speaking = reactive(False)

    # Model live stats
    token_speed = reactive(backend.token_speed)

    # Pending reactive for backward compat
    vad_state = reactive(backend.vad_state)
    wake_word_armed = reactive(backend.wake_word_armed)
    memory_stats = reactive(backend.memory_stats)
    active_skills = reactive(backend.active_skills)

    def on_mount(self) -> None:
        self.set_interval(2.0, self._update_tts_stats)
        self.set_interval(2.0, self._update_system_stats)
        self.set_interval(10.0, self._update_git_stats)
        self.set_interval(2.0, self._update_model_stats)
        self._update_system_stats()
        self._update_git_stats()
        self._update_tts_stats()
        self._update_model_stats()

    def _update_git_stats(self) -> None:
        try:
            cwd = os.getcwd()
            self.git_branch = subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=cwd,
                stderr=subprocess.DEVNULL, text=True,
            ).strip()
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=cwd,
                stderr=subprocess.DEVNULL, text=True,
            )
            self.git_uncommitted = len([l for l in status.splitlines() if l.strip()])
            self.git_last_commit = subprocess.check_output(
                ["git", "log", "-1", "--format=%s"], cwd=cwd,
                stderr=subprocess.DEVNULL, text=True,
            ).strip()
        except Exception:
            self.git_branch = ""
            self.git_uncommitted = 0
            self.git_last_commit = ""
        self._refresh_widgets()

    def _update_system_stats(self) -> None:
        try:
            cpu = int(psutil.cpu_percent())
            self.cpu_history = self.cpu_history[1:] + [cpu]

            mem = int(psutil.virtual_memory().percent)
            self.mem_history = self.mem_history[1:] + [mem]

            du = shutil.disk_usage("/")
            disk = int(du.used / du.total * 100)
            self.disk_history = self.disk_history[1:] + [disk]

            uptime_secs = time.time() - psutil.boot_time()
            days = int(uptime_secs // (24 * 3600))
            hours = int((uptime_secs % (24 * 3600)) // 3600)
            minutes = int((uptime_secs % 3600) // 60)
            if days > 0:
                self.uptime_str = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                self.uptime_str = f"{hours}h {minutes}m"
            else:
                self.uptime_str = f"{minutes}m"
        except Exception:
            pass
        self._refresh_widgets()

    def _update_tts_stats(self) -> None:
        try:
            self.tts_speaking = is_speaking()
            self.tts_queue = get_queue_size()
            self.tts_latency = get_last_latency_ms()
            self.tts_volume = int(get_volume() * 100)
            self.tts_status = get_tts_status()
        except Exception:
            pass
        self._refresh_widgets()

    def _update_model_stats(self) -> None:
        self.token_speed = backend.token_speed or 0.0
        self._refresh_widgets()

    def _refresh_widgets(self) -> None:
        try:
            # 1. Active Goal
            goal_text = "Build Spidy AI"
            status_text = {
                "idle": "Idle",
                "generating": "Speaking...",
                "playing": "Playing...",
            }.get(self.tts_status, self.tts_status)
            self._set_text("#goal-widget-1", goal_text)
            self._set_text("#goal-widget-2", f"TTS: [cyan]{status_text}[/cyan]")
            self._set_text(
                "#goal-widget-3",
                f"Queue: [cyan]{self.tts_queue}[/cyan]  "
                f"Latency: [cyan]{self.tts_latency}ms[/cyan]",
            )

            # 2. Current Project
            if self.git_branch:
                self._set_text("#proj-name", f"Name      [cyan]{os.path.basename(os.getcwd())}[/cyan]")
                self._set_text("#proj-branch", f"Branch    [cyan]{self.git_branch}[/cyan]")
                self._set_text("#proj-pending", f"Pending   [cyan]{self.git_uncommitted} changes[/cyan]")
                self._set_display("#proj-widget", True)
            else:
                self._set_display("#proj-widget", False)

            # 3. Model Status
            provider_label = {"openrouter": "OpenRouter", "ollama": "Ollama"}.get(
                backend.provider_name, backend.provider_name or "N/A"
            )
            model_label = backend.model_name or "N/A"
            speed_label = f"{self.token_speed} t/s" if self.token_speed else "N/A"

            self._set_text("#model-active", f"Active     [cyan]{model_label}[/cyan]")
            self._set_text("#model-provider", f"Provider   [cyan]{provider_label}[/cyan]")
            self._set_text("#model-speed", f"Speed      [cyan]{speed_label}[/cyan]")
            online = backend.ollama_connected
            online_label = "[green]Online[/green]" if online else "[red]Offline[/red]"
            self._set_text("#model-online", f"Network    {online_label}")

            # 4. TTS Status
            if backend.tts_enabled:
                speaking_label = "[green]Speaking[/green]" if self.tts_speaking else "Idle"
                engine_label = get_tts_engine()
                self._set_text("#tts-engine", f"Engine     [cyan]{engine_label}[/cyan]")
                self._set_text("#tts-vol", f"Volume     [cyan]{self.tts_volume}%[/cyan]")
                self._set_text("#tts-queue", f"Queue      [cyan]{self.tts_queue}[/cyan]")
                self._set_text("#tts-latency", f"Latency    [cyan]{self.tts_latency}ms[/cyan]")
                self._set_text("#tts-state", f"State      {speaking_label}")
                self._set_display("#tts-widget", True)
            else:
                self._set_display("#tts-widget", False)

            # 5. Git Status
            if self.git_branch:
                self._set_text("#git-branch-val", f"Branch       [cyan]{self.git_branch}[/cyan]")
                self._set_text("#git-uncom-val", f"Uncommitted  [cyan]{self.git_uncommitted}[/cyan]")
                short_commit = self.git_last_commit[:20] + "..." if len(self.git_last_commit) > 20 else self.git_last_commit
                self._set_text("#git-last-val", f"Last Commit  [cyan]{short_commit}[/cyan]")
                self._set_display("#git-widget", True)
            else:
                self._set_display("#git-widget", False)

            # 6. System Health
            self._set_text("#sys-cpu-val", f"CPU Usage      [cyan]{self.cpu_history[-1]}%[/cyan]  {make_sparkline(self.cpu_history)}")
            self._set_text("#sys-mem-val", f"Memory         [cyan]{self.mem_history[-1]}%[/cyan]  {make_sparkline(self.mem_history)}")
            self._set_text("#sys-disk-val", f"Disk           [cyan]{self.disk_history[-1]}%[/cyan]  {make_sparkline(self.disk_history)}")
            self._set_text("#sys-uptime-val", f"Uptime         [cyan]{self.uptime_str}[/cyan]")

            # 7. Quick Actions (static, always visible)
            # 8. Key Bindings (static, always visible)
        except Exception:
            pass

    def _set_text(self, selector: str, text: str) -> None:
        try:
            self.query_one(selector, Label).update(text)
        except Exception:
            pass

    def _set_display(self, selector: str, visible: bool) -> None:
        try:
            w = self.query_one(selector, Vertical)
            w.display = visible
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="sidebar-container"):
            # Header
            with Horizontal(classes="sidebar-header-row"):
                yield Label("CONTEXT", classes="sidebar-title")
                yield Label("✕", classes="sidebar-close-btn")

            # 1. Active Goal
            with Vertical(classes="sidebar-widget", id="goal-widget"):
                yield Label("[goal:active]", classes="widget-header")
                yield Label("Build Spidy AI", id="goal-widget-1", classes="widget-item-stat")
                yield Label("TTS: Idle", id="goal-widget-2", classes="widget-item-stat")
                yield Label("Queue: 0  Latency: 0ms", id="goal-widget-3", classes="widget-item-stat")

            # 2. Current Project
            with Vertical(classes="sidebar-widget", id="proj-widget"):
                yield Label("[project:current]", classes="widget-header")
                yield Label("Name      [cyan]...[/cyan]", id="proj-name", classes="widget-item-stat")
                yield Label("Branch    [cyan]...[/cyan]", id="proj-branch", classes="widget-item-stat")
                yield Label("Pending   [cyan]...[/cyan]", id="proj-pending", classes="widget-item-stat")

            # 3. Model Status (real data)
            with Vertical(classes="sidebar-widget", id="model-widget"):
                yield Label("[model:status]", classes="widget-header")
                yield Label("Active     [cyan]...[/cyan]", id="model-active", classes="widget-item-stat")
                yield Label("Provider   [cyan]...[/cyan]", id="model-provider", classes="widget-item-stat")
                yield Label("Speed      [cyan]...[/cyan]", id="model-speed", classes="widget-item-stat")
                yield Label("Network    [cyan]...[/cyan]", id="model-online", classes="widget-item-stat")

            # 4. TTS Status (real data)
            with Vertical(classes="sidebar-widget", id="tts-widget"):
                yield Label("[tts:status]", classes="widget-header")
                yield Label("Engine     [cyan]...[/cyan]", id="tts-engine", classes="widget-item-stat")
                yield Label("Volume     [cyan]...[/cyan]", id="tts-vol", classes="widget-item-stat")
                yield Label("Queue      [cyan]...[/cyan]", id="tts-queue", classes="widget-item-stat")
                yield Label("Latency    [cyan]...[/cyan]", id="tts-latency", classes="widget-item-stat")
                yield Label("State      [cyan]...[/cyan]", id="tts-state", classes="widget-item-stat")

            # 5. Git Status (real data)
            with Vertical(classes="sidebar-widget", id="git-widget"):
                yield Label("[git:status]", classes="widget-header")
                yield Label("Branch       [cyan]...[/cyan]", id="git-branch-val", classes="widget-item-stat")
                yield Label("Uncommitted  [cyan]...[/cyan]", id="git-uncom-val", classes="widget-item-stat")
                yield Label("Last Commit  [cyan]...[/cyan]", id="git-last-val", classes="widget-item-stat")

            # 6. System Health (real data)
            with Vertical(classes="sidebar-widget", id="sys-widget"):
                yield Label("[system:health]", classes="widget-header")
                yield Label("CPU Usage      [cyan]0%[/cyan]", id="sys-cpu-val", classes="widget-item-stat")
                yield Label("Memory         [cyan]0%[/cyan]", id="sys-mem-val", classes="widget-item-stat")
                yield Label("Disk           [cyan]0%[/cyan]", id="sys-disk-val", classes="widget-item-stat")
                yield Label("Uptime         [cyan]0m[/cyan]", id="sys-uptime-val", classes="widget-item-stat")

            # 7. Quick Actions
            with Vertical(classes="sidebar-widget", id="actions-widget"):
                yield Label("[quick:actions]", classes="widget-header")
                yield Label("[red]F1[/red] Help    [red]F2[/red] Voice", classes="widget-item-stat")
                yield Label("[red]F3[/red] Browser [red]F4[/red] Terminal", classes="widget-item-stat")
                yield Label("[red]F5[/red] Reload", classes="widget-item-stat")

    def update_context_stats(self, token_count: int) -> None:
        pass

    def watch_vad_state(self, value: str) -> None:
        pass

    def watch_wake_word_armed(self, value: bool) -> None:
        pass

    def watch_token_speed(self, value: float) -> None:
        pass

    def watch_memory_stats(self, value: dict) -> None:
        pass

    def watch_active_skills(self, value: dict) -> None:
        pass

    def update_speed(self, speed: float) -> None:
        pass
