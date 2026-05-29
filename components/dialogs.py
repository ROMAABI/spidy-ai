from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label
from textual.widgets.option_list import Option
from spidy_tui.backend import backend

class SpidyCommandDialog(ModalScreen[str]):
    """The command palette overlay."""
    
    SPIDY_COMMANDS = [
        {"name": "/clear", "desc": "Clear chat history"},
        {"name": "/memory", "desc": "Show memory browser"},
        {"name": "/voice", "desc": "Toggle voice input mode"},
        {"name": "/model", "desc": "Switch LLM model (e.g. /model qwen)"},
        {"name": "/skill", "desc": "Manually invoke a skill"},
        {"name": "/theme", "desc": "Switch color theme"},
        {"name": "/export", "desc": "Export session to markdown"},
        {"name": "/sidebar", "desc": "Toggle sidebar"},
        {"name": "/think", "desc": "Toggle reasoning display"},
        {"name": "/tts", "desc": "Toggle TTS output"},
    ]

    def compose(self) -> ComposeResult:
        yield Label("Command Palette (Esc to close)", classes="dialog-header")
        yield Input(placeholder="Type a command...", id="command-input")
        options = [Option(f"{cmd['name']} - {cmd['desc']}", id=cmd['name']) for cmd in self.SPIDY_COMMANDS]
        yield OptionList(*options, id="command-list")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        search = event.value.lower()
        option_list = self.query_one(OptionList)
        option_list.clear_options()
        for cmd in self.SPIDY_COMMANDS:
            if search in cmd["name"].lower() or search in cmd["desc"].lower():
                option_list.add_option(Option(f"{cmd['name']} - {cmd['desc']}", id=cmd['name']))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value
        # If it matches exactly or has args, return it
        if val.startswith("/"):
            self.dismiss(val)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class HelpDialog(ModalScreen[None]):
    """Help dialog showing keybinds."""
    def compose(self) -> ComposeResult:
        yield Label("Spidy AI Help", classes="dialog-header")
        help_text = """
[bold]Keybinds[/bold]
Enter        Send message
Shift+Enter  New line in prompt
Ctrl+C       Confirm exit
Ctrl+L       Clear chat
Ctrl+S       Toggle sidebar
Ctrl+T       Toggle TTS
Ctrl+V       Toggle voice input mode
j / k        Navigate messages (when prompt not focused)
g / G        Jump to first / last message
t            Toggle thinking blocks
T            Toggle timestamps
/            Open command palette
F1           Show this help
Esc          Close dialogs / cancel
        """
        yield Label(help_text)
        yield Label("Press Esc to close", classes="dialog-footer")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class ExitDialog(ModalScreen[bool]):
    """Confirm exit dialog."""
    def compose(self) -> ComposeResult:
        yield Label("Are you sure you want to exit? (y/N)", classes="dialog-header")

    def on_key(self, event) -> None:
        if event.key.lower() == "y":
            self.dismiss(True)
        elif event.key == "escape" or event.key.lower() == "n":
            self.dismiss(False)
