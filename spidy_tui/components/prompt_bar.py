from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label
from textual.message import Message
from spidy_tui.backend import backend

class SpidyPrompt(Widget):
    """The horizontal input prompt block with right-aligned tips and send icon."""

    wake_word_armed = reactive(backend.wake_word_armed)
    vad_state = reactive(backend.vad_state)

    def compose(self) -> ComposeResult:
        with Horizontal(id="prompt-row-container"):
            yield Label(">", id="prompt-chevron")
            yield Input(placeholder="Type command or message...", id="prompt-input", classes="spidy-input")
            with Horizontal(id="prompt-tips-container"):
                yield Label("↵ Enter to send", classes="prompt-tip")
                yield Label("  ", classes="prompt-tip-space")
                yield Label("⇧ Enter for new line", classes="prompt-tip")
                yield Label("  ", classes="prompt-tip-space")
                yield Label("➤", id="prompt-send-btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.post_message(self.Submitted(text))
        event.input.value = ""

    def update_model_info(self) -> None:
        pass

    def update_stats(self, token_count: int) -> None:
        pass

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()
