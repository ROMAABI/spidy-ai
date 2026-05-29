from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static
import asyncio

from spidy_tui.components.header import SpidyHeader
from spidy_tui.components.footer import SpidyFooter
from spidy_tui.components.sidebar import SpidySidebar
from spidy_tui.components.chat_view import ChatView
from spidy_tui.components.prompt_bar import SpidyPrompt
from spidy_tui.components.dialogs import SpidyCommandDialog, HelpDialog, ExitDialog
from spidy_tui.backend import backend

class SplashScreen(Screen):
    """The splash screen shown on startup."""
    def compose(self) -> ComposeResult:
        logo = """
   _____       _     _          ___  _____ 
  / ____|     (_)   | |        / _ \\|_   _|
 | (___  _ __  _  __| |_   _  | (_) | | |  
  \\___ \\| '_ \\| |/ _` | | | |  > _ <  | |  
  ____) | |_) | | (_| | |_| | | (_) |_| |_ 
 |_____/| .__/|_|\\__,_|\\__, |  \\___/|_____|
        | |             __/ |              
        |_|            |___/               
        """
        yield Static(logo, id="splash-logo")
        yield Static("Initializing modules...", id="splash-text")

    def on_mount(self) -> None:
        self.set_timer(1.5, self.app.pop_screen)


class SessionScreen(Screen):
    """The main chat session screen."""
    
    BINDINGS = [
        Binding("ctrl+c", "request_quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+t", "toggle_tts", "TTS"),
        Binding("ctrl+v", "toggle_voice", "Voice"),
        Binding("slash", "command_palette", "Command"),
        Binding("f1", "help", "Help"),
        Binding("j", "nav_down", "Down", show=False),
        Binding("k", "nav_up", "Up", show=False),
        Binding("g", "nav_top", "Top", show=False),
        Binding("G", "nav_bottom", "Bottom", show=False),
        Binding("t", "toggle_thinking", "Think", show=False),
        Binding("T", "toggle_timestamps", "Time", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield SpidyHeader()
        with Horizontal():
            with Container(id="main-area"):
                yield ChatView(id="chat-view")
                yield SpidyPrompt(id="prompt-bar")
            yield SpidySidebar(id="sidebar")
        yield SpidyFooter()

    def on_mount(self) -> None:
        # Check terminal size to hide sidebar if too narrow
        self.check_sidebar_visibility()
        # Set up backend callbacks
        backend.on_vad_state_change = self.on_vad_changed
        backend.on_wake_word_state_change = self.on_wake_word_changed

    def on_resize(self, event) -> None:
        self.check_sidebar_visibility()

    def check_sidebar_visibility(self) -> None:
        sidebar = self.query_one(SpidySidebar)
        if self.app.size.width < 100:
            sidebar.add_class("hidden")
        else:
            sidebar.remove_class("hidden")

    def on_spidy_prompt_submitted(self, message: SpidyPrompt.Submitted) -> None:
        text = message.text
        if text.startswith("/"):
            self.handle_command(text)
            return

        chat_view = self.query_one(ChatView)
        chat_view.add_user_message(text)
        
        # Start streaming response
        asyncio.create_task(self.stream_response(text))
        
    def handle_command(self, cmd: str) -> None:
        parts = cmd.split(" ", 1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        chat_view = self.query_one(ChatView)
        
        if action == "/clear":
            chat_view.clear_messages()
            self.app.notify("Chat cleared")
        elif action == "/sidebar":
            self.action_toggle_sidebar()
        elif action == "/tts":
            self.action_toggle_tts()
        elif action == "/voice":
            self.action_toggle_voice()
        elif action == "/model":
            if args:
                backend.model_name = args
                self.app.notify(f"Model set to {args}")
            else:
                self.app.notify("Usage: /model <name>")
        elif action == "/think":
            self.action_toggle_thinking()
        elif action == "/theme":
            self.app.theme = "textual-light" if self.app.theme == "textual-dark" else "textual-dark"
            self.app.notify(f"Theme switched to {'Dark' if self.app.theme == 'textual-dark' else 'Light'}")
        else:
            self.app.notify(f"Unknown command: {action}")

    async def stream_response(self, prompt: str) -> None:
        chat_view = self.query_one(ChatView)
        
        # Add a small delay for realism
        await asyncio.sleep(0.2)
        chat_view.start_assistant_message()
        
        async for chunk in backend.stream_chat_response(prompt):
            if chunk["type"] == "thinking_start":
                chat_view.start_thinking()
            elif chunk["type"] == "thinking_token":
                chat_view.append_thinking_token(chunk["content"])
            elif chunk["type"] == "thinking_end":
                chat_view.end_thinking()
            elif chunk["type"] == "skill_start":
                # We can just show skill in progress, but we'll wait for end
                pass
            elif chunk["type"] == "skill_end":
                chat_view.add_skill_call(chunk["skill_name"], chunk.get("result", ""))
            elif chunk["type"] == "message_token":
                chat_view.append_assistant_token(chunk["content"])

    def on_vad_changed(self, state: str) -> None:
        # VAD state triggers an update automatically via reactive variable on PromptBar and Sidebar
        pass

    def on_wake_word_changed(self, state: bool) -> None:
        if state:
            self.app.notify("Microphone Armed")
        else:
            self.app.notify("Microphone Disarmed")

    # Actions
    def action_request_quit(self) -> None:
        def check_quit(quit: bool | None) -> None:
            if quit:
                self.app.exit()
        self.app.push_screen(ExitDialog(), check_quit)

    def action_clear_chat(self) -> None:
        self.query_one(ChatView).clear_messages()
        
    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(SpidySidebar)
        if sidebar.has_class("hidden"):
            sidebar.remove_class("hidden")
        else:
            sidebar.add_class("hidden")

    def action_toggle_tts(self) -> None:
        backend.tts_enabled = not backend.tts_enabled
        self.app.notify("TTS Enabled" if backend.tts_enabled else "TTS Disabled")
        
    def action_toggle_voice(self) -> None:
        asyncio.create_task(backend.toggle_wake_word())

    def action_command_palette(self) -> None:
        # Only open if prompt bar doesn't have focus, OR just open it anyway
        def exec_command(cmd: str | None) -> None:
            if cmd:
                self.handle_command(cmd)
        self.app.push_screen(SpidyCommandDialog(), exec_command)

    def action_help(self) -> None:
        self.app.push_screen(HelpDialog())

    def action_nav_down(self) -> None:
        self.query_one(ChatView).navigate_down()

    def action_nav_up(self) -> None:
        self.query_one(ChatView).navigate_up()

    def action_nav_top(self) -> None:
        self.query_one(ChatView).navigate_top()

    def action_nav_bottom(self) -> None:
        self.query_one(ChatView).navigate_bottom()

    def action_toggle_thinking(self) -> None:
        cv = self.query_one(ChatView)
        cv.show_thinking = not cv.show_thinking

    def action_toggle_timestamps(self) -> None:
        cv = self.query_one(ChatView)
        cv.show_timestamps = not cv.show_timestamps


class SpidyTUIApp(App):
    """Spidy AI Textual Application."""
    
    CSS_PATH = "app.tcss"
    TITLE = "Spidy AI"
    
    def on_mount(self) -> None:
        self.push_screen(SessionScreen())
        self.push_screen(SplashScreen())

if __name__ == "__main__":
    app = SpidyTUIApp()
    app.run()
