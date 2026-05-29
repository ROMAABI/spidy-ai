from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Label
from textual.message import Message

class QuickCommandItem(Widget):
    """A single interactive quick command panel."""
    
    def __init__(self, cmd: str, desc: str):
        super().__init__()
        self.cmd = cmd
        self.desc = desc
        self.add_class("quick-command-item")
        
    def compose(self) -> ComposeResult:
        with Vertical(classes="qc-item-container"):
            yield Label(self.cmd, classes="qc-cmd")
            yield Label(self.desc, classes="qc-desc")
            
    def on_click(self) -> None:
        self.post_message(self.Clicked(self.cmd))
        
    class Clicked(Message):
        def __init__(self, cmd: str) -> None:
            self.cmd = cmd
            super().__init__()


class QuickCommands(Widget):
    """Horizontal row container for quick action command items."""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="quick-commands-row"):
            yield QuickCommandItem("/summarize", "Summarize context")
            yield QuickCommandItem("/check", "Check system")
            yield QuickCommandItem("/clear", "Clear conversation")
            yield QuickCommandItem("/help", "Show commands")
