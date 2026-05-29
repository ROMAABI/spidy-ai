from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from spidy_tui.backend import backend

class SpidySidebar(Widget):
    """The sidebar component."""
    
    vad_state = reactive(backend.vad_state)
    wake_word_armed = reactive(backend.wake_word_armed)
    token_speed = reactive(backend.token_speed)
    memory_stats = reactive(backend.memory_stats)
    active_skills = reactive(backend.active_skills)

    def watch_vad_state(self, value: str) -> None:
        self.update_voice()

    def watch_wake_word_armed(self, value: bool) -> None:
        self.update_voice()

    def watch_token_speed(self, value: float) -> None:
        self.update_llm()
        
    def watch_memory_stats(self, value: dict) -> None:
        self.update_memory()

    def watch_active_skills(self, value: dict) -> None:
        self.update_skills()

    def update_voice(self) -> None:
        armed_str = "[green]Armed[/]" if self.wake_word_armed else "[dim]Disarmed[/]"
        vad_colors = {"idle": "dim", "listening": "red", "processing": "yellow"}
        color = vad_colors.get(self.vad_state, "white")
        vad_str = f"[{color}]{self.vad_state.capitalize()}[/]"
        try:
            self.query_one("#voice-stats", Label).update(f"Wake: {armed_str}\nVAD: {vad_str}")
        except Exception:
            pass

    def update_memory(self) -> None:
        try:
            self.query_one("#memory-stats", Label).update(
                f"RAM: {self.memory_stats['ram_usage_mb']} MB\n"
                f"Vectors: {self.memory_stats['chromadb_vectors']}\n"
                f"Rows: {self.memory_stats['sqlite_rows']}"
            )
        except Exception:
            pass

    def update_llm(self) -> None:
        try:
            self.query_one("#llm-stats", Label).update(
                f"Model: {backend.model_name}\n"
                f"Speed: {self.token_speed:.1f} tok/s"
            )
        except Exception:
            pass

    def update_skills(self) -> None:
        try:
            skills_str = ""
            for skill, active in self.active_skills.items():
                indicator = "🟢" if active else "⚫"
                skills_str += f"{indicator} {skill}\n"
            self.query_one("#skills-stats", Label).update(skills_str.strip())
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Vertical(classes="sidebar-section"):
            yield Label("🧠 Memory", classes="sidebar-title")
            yield Label(
                f"RAM: {self.memory_stats['ram_usage_mb']} MB\n"
                f"Vectors: {self.memory_stats['chromadb_vectors']}\n"
                f"Rows: {self.memory_stats['sqlite_rows']}",
                id="memory-stats"
            )

        with Vertical(classes="sidebar-section"):
            yield Label("🎤 Voice", classes="sidebar-title")
            armed_str = "[green]Armed[/]" if self.wake_word_armed else "[dim]Disarmed[/]"
            vad_str = f"[dim]{self.vad_state.capitalize()}[/]"
            yield Label(f"Wake: {armed_str}\nVAD: {vad_str}", id="voice-stats")

        with Vertical(classes="sidebar-section"):
            yield Label("⚡ Skills", classes="sidebar-title")
            skills_str = ""
            for skill, active in self.active_skills.items():
                indicator = "🟢" if active else "⚫"
                skills_str += f"{indicator} {skill}\n"
            yield Label(skills_str.strip(), id="skills-stats")

        with Vertical(classes="sidebar-section"):
            yield Label("🔗 LLM", classes="sidebar-title")
            yield Label(
                f"Model: {backend.model_name}\n"
                f"Speed: {self.token_speed:.1f} tok/s",
                id="llm-stats"
            )
