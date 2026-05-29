from textual.app import ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static
from datetime import datetime
from spidy_tui.backend import backend

class ChatMessage(Widget):
    """A single chat message with reactive streaming."""

    show_timestamp = reactive(False)
    show_thinking = reactive(True)
    generation_time = reactive(0.0)

    def __init__(self, role: str, content: str = ""):
        super().__init__()
        self.role = role
        self._text_content = content
        self._thinking_content = ""
        self.skills: list[tuple[str, str]] = []
        self.steps = []
        self._time_str = datetime.now().strftime("%I:%M %p")
        self.add_class(self.role)

    def watch_show_thinking(self, value: bool) -> None:
        self._update_thinking()

    def append_thinking(self, token: str) -> None:
        self._thinking_content += token
        self._update_thinking()

    def append_content(self, token: str) -> None:
        self._text_content += token
        try:
            self.query_one("#msg-content", Label).update(self._text_content)
        except Exception:
            pass

    def start_step(self, name: str) -> None:
        title = self._get_step_title(name)
        for s in self.steps:
            if s["name"] == name:
                s["status"] = "IN PROGRESS"
                self._update_steps_ui()
                return
        self.steps.append({"name": name, "title": title, "status": "IN PROGRESS"})
        self._update_steps_ui()

    def end_step(self, name: str, result: str) -> None:
        title = self._get_step_title(name)
        for s in self.steps:
            if s["name"] == name:
                s["status"] = "DONE"
                self._update_steps_ui()
                return
        self.steps.append({"name": name, "title": title, "status": "DONE"})
        self._update_steps_ui()

    def _get_step_title(self, name: str) -> str:
        mapping = {
            "clipboard": "Accessing clipboard logs",
            "screenshot": "Checking screen diagnostics",
            "search": "Checking API limits",
            "code_executor": "Fetching system logs for commit",
        }
        return mapping.get(name, f"Executing skill: {name}")

    def _update_steps_ui(self) -> None:
        try:
            container = self.query_one("#steps-container", Container)
            container.display = len(self.steps) > 0
            container.remove_children()
            for step in self.steps:
                icon = "✓" if step["status"] == "DONE" else ("⟳" if step["status"] == "IN PROGRESS" else "◯")
                cls = "step-done" if step["status"] == "DONE" else ("step-progress" if step["status"] == "IN PROGRESS" else "step-pending")
                container.mount(Horizontal(
                    Label(f"{icon} {step['title']}", classes=f"step-title {cls}"),
                    Label(step["status"].rjust(15), classes=f"step-status {cls}"),
                    classes="step-row"
                ))
        except Exception:
            pass

    def add_thinking_block(self) -> None:
        try:
            self.query_one("#thinking-block").display = self.show_thinking
        except Exception:
            pass

    def end_thinking_block(self) -> None:
        self._update_thinking()

    def _update_thinking(self) -> None:
        try:
            tb = self.query_one("#thinking-block", Static)
            if self._thinking_content:
                content = self._thinking_content.strip()
                if not content.lower().startswith("thought:"):
                    display_text = f"Thought: {content}"
                else:
                    display_text = content
                tb.update(display_text)
                tb.display = self.show_thinking
            else:
                tb.display = False
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        if self.role == "user":
            with Vertical(classes="user-bubble-container"):
                yield Label(f"YOU  {self._time_str}", classes="user-header")
                yield Label(self._text_content, id="msg-content", classes="message-content")
        else:
            with Horizontal(classes="assistant-msg-row"):
                yield Label("🕸", classes="assistant-avatar")
                with Vertical(classes="assistant-bubble-container"):
                    yield Label(f"SPIDY  {self._time_str}", classes="assistant-header")
                    yield Static(self._thinking_content, id="thinking-block", classes="thinking-block")
                    yield Container(id="steps-container")
                    yield Label(self._text_content, id="msg-content", classes="message-content")
                    yield Label("", id="assistant-footer", classes="assistant-footer")

    def on_mount(self) -> None:
        self.update_footer()
        self._update_thinking()
        self._update_steps_ui()

    def watch_generation_time(self, val: float) -> None:
        self.update_footer()

    def update_footer(self) -> None:
        if self.role == "assistant":
            try:
                footer = self.query_one("#assistant-footer", Label)
                model = backend.model_name
                provider = backend.provider_name
                
                if provider == "openrouter":
                    display = "DeepSeek v4 Flash · OpenRouter"
                elif model == "gemma4:e2b":
                    display = "Sisyphus · MiMo V2.5 Free"
                else:
                    display = f"{model} · {provider}"
                
                time_str = f" · {self.generation_time:.1f}s" if self.generation_time > 0 else ""
                footer.update(f"▋ {display}{time_str}")
            except Exception:
                pass


class ChatView(VerticalScroll):
    """The main chat area containing messages."""

    show_timestamps = reactive(False)
    show_thinking = reactive(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_message: ChatMessage | None = None

    def compose(self) -> ComposeResult:
        yield Label(rf"\[ sys_init: session started {datetime.now().strftime('%H:%M')} AM ]", classes="system-init-log")

    def watch_show_thinking(self, value: bool) -> None:
        for msg in self.query(ChatMessage):
            msg.show_thinking = value

    def add_user_message(self, content: str) -> None:
        msg = ChatMessage(role="user", content=content)
        msg.show_thinking = self.show_thinking
        self.mount(msg)
        self.scroll_end(animate=False)
        self.current_message = None

    def start_assistant_message(self) -> None:
        msg = ChatMessage(role="assistant", content="")
        msg.show_thinking = self.show_thinking
        self.mount(msg)
        self.current_message = msg
        self.scroll_end(animate=False)

    def append_assistant_token(self, token: str) -> None:
        if self.current_message:
            self.current_message.append_content(token)
            self.scroll_end(animate=False)

    def start_thinking(self) -> None:
        if self.current_message:
            self.current_message.add_thinking_block()
            self.scroll_end(animate=False)

    def append_thinking_token(self, token: str) -> None:
        if self.current_message:
            self.current_message.append_thinking(token)
            self.scroll_end(animate=False)

    def end_thinking(self) -> None:
        if self.current_message:
            self.current_message.end_thinking_block()
            self.scroll_end(animate=False)

    def start_skill(self, name: str) -> None:
        if self.current_message:
            self.current_message.start_step(name)
            self.scroll_end(animate=False)

    def end_skill(self, name: str, result: str) -> None:
        if self.current_message:
            self.current_message.end_step(name, result)
            self.scroll_end(animate=False)

    def end_assistant_message(self) -> None:
        self.current_message = None
        self.scroll_end(animate=False)

    def clear_messages(self) -> None:
        self.remove_children()
        # Re-add system init log
        self.mount(Label(rf"\[ sys_init: session started {datetime.now().strftime('%H:%M')} AM ]", classes="system-init-log"))
        self.current_message = None

    def navigate_down(self) -> None:
        self.scroll_end(animate=True)

    def navigate_up(self) -> None:
        self.scroll_up(animate=True)

    def navigate_top(self) -> None:
        self.scroll_home(animate=True)

    def navigate_bottom(self) -> None:
        self.scroll_end(animate=True)
