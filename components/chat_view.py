from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static
from datetime import datetime

class ChatMessage(Widget):
    """A single chat message bubble."""
    
    show_timestamp = reactive(False)
    show_thinking = reactive(True)

    def __init__(self, role: str, content: str = ""):
        super().__init__()
        self.role = role
        self.text_content = content
        self.thinking_content = ""
        self.skills: list[tuple[str, str]] = [] # list of (skill_name, result)
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        self.add_class(self.role)

    def watch_show_timestamp(self, value: bool) -> None:
        try:
            ts_label = self.query_one(".message-header", Label)
            ts_label.display = value
        except Exception:
            pass

    def watch_show_thinking(self, value: bool) -> None:
        try:
            for tb in self.query(".thinking-block"):
                if value:
                    tb.remove_class("hidden")
                else:
                    tb.add_class("hidden")
        except Exception:
            pass

    def append_thinking(self, token: str) -> None:
        self.thinking_content += token
        self._update_ui()

    def append_content(self, token: str) -> None:
        self.text_content += token
        self._update_ui()

    def add_skill_call(self, name: str, result: str) -> None:
        self.skills.append((name, result))
        self._update_ui()
        
    def add_thinking_block(self) -> None:
        self.mount(Static("Thinking...", classes="thinking-block"))
        
    def end_thinking_block(self) -> None:
        try:
            tb = self.query(".thinking-block").last()
            if tb:
                tb.update(f"💭 {self.thinking_content}")  # type: ignore
        except Exception:
            pass

    def _update_ui(self) -> None:
        try:
            content_label = self.query_one(".message-content", Label)
            content_label.update(self.text_content)
            
            # Mount new skills if they don't have widgets
            # Simplistic approach: clear and remount skills? 
            # Or just update existing. For now, we only handle simple streaming
            # The complex part is mounting new widgets dynamically. We handle this in ChatView instead for skills.
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Label(self.timestamp, classes="message-header")
        
        if self.thinking_content:
            yield Static(f"💭 {self.thinking_content}", classes="thinking-block")
            
        for name, result in self.skills:
            yield Static(f"⚡ {name}\n> {result}", classes="skill-block")
            
        yield Label(self.text_content, classes="message-content")


class ChatView(VerticalScroll):
    """The main chat area containing messages."""
    
    show_timestamps = reactive(False)
    show_thinking = reactive(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_message: ChatMessage | None = None
        self.focus_index = -1
        self.can_focus = True

    def watch_show_timestamps(self, value: bool) -> None:
        for msg in self.query(ChatMessage):
            msg.show_timestamp = value

    def watch_show_thinking(self, value: bool) -> None:
        for msg in self.query(ChatMessage):
            msg.show_thinking = value
            
    def add_user_message(self, content: str) -> None:
        msg = ChatMessage(role="user", content=content)
        msg.show_timestamp = self.show_timestamps
        msg.show_thinking = self.show_thinking
        self.mount(msg)
        self.scroll_end(animate=False)
        self.current_message = None # Reset current streaming message

    def start_assistant_message(self) -> None:
        msg = ChatMessage(role="assistant", content="")
        msg.show_timestamp = self.show_timestamps
        msg.show_thinking = self.show_thinking
        self.mount(msg)
        self.current_message = msg
        self.scroll_end(animate=False)

    def append_assistant_token(self, token: str) -> None:
        if self.current_message:
            self.current_message.append_content(token)
            # Only scroll to end if we are already at the bottom
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

    def add_skill_call(self, name: str, result: str) -> None:
        if self.current_message:
            # Mount a skill block directly to the current message
            self.current_message.mount(Static(f"⚡ {name}\n> {result}", classes="skill-block"), before=".message-content")
            self.scroll_end(animate=False)
            
    def clear_messages(self) -> None:
        for msg in self.query(ChatMessage):
            msg.remove()
        self.current_message = None

    def navigate_up(self) -> None:
        messages = list(self.query(ChatMessage))
        if not messages: return
        self.focus_index = max(0, self.focus_index - 1) if self.focus_index >= 0 else len(messages) - 1
        self.scroll_to_widget(messages[self.focus_index])

    def navigate_down(self) -> None:
        messages = list(self.query(ChatMessage))
        if not messages: return
        if self.focus_index < 0: return
        self.focus_index = min(len(messages) - 1, self.focus_index + 1)
        self.scroll_to_widget(messages[self.focus_index])

    def navigate_top(self) -> None:
        messages = list(self.query(ChatMessage))
        if not messages: return
        self.focus_index = 0
        self.scroll_to_widget(messages[self.focus_index])

    def navigate_bottom(self) -> None:
        messages = list(self.query(ChatMessage))
        if not messages: return
        self.focus_index = len(messages) - 1
        self.scroll_to_widget(messages[self.focus_index])
