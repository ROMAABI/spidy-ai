import asyncio
import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static

from spidy_tui.backend import backend
from spidy_tui.components.chat_view import ChatMessage, ChatView
from spidy_tui.components.dialogs import ExitDialog, HelpDialog, SpidyCommandDialog
from spidy_tui.components.footer import SpidyFooter
from spidy_tui.components.header import SpidyHeader
from spidy_tui.components.prompt_bar import SpidyPrompt
from spidy_tui.components.quick_commands import QuickCommandItem, QuickCommands
from spidy_tui.components.sidebar import SpidySidebar
from spidy_tui.theme_manager import (
    SpidyThemeColors,
    ThemeManager,
    _best_text_color,
    _parse_hex,
)


class SplashScreen(Screen):
    def compose(self) -> ComposeResult:
        spider = r"""
        ⠀⠀⠀⠀⠀⠀⠀⢀⠆⠀⢀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡀⠀⠰⡀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⢠⡏⠀⢀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⡀⠀⢹⣄⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⣰⡟⠀⠀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀⠀⢻⣆⠀⠀⠀⠀⡔
        ⠀⠀⠀⠀⢠⣿⠁⠀⣸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡊⣿⣇⠀⠈⣿⡆⠀⡠⠊⠀
        ⠀⠀⠀⠀⣾⡇⠀⢀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡐⠀⢸⣿⡀⠀⢸⣿⠁⠀⠀⠀
        ⠀⠀⠀⢸⣿⠀⠀⣸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⢸⣿⣇⠀⠄⣿⡇⠀⠀⠀
        ⠀⠀⠀⣿⣿⠀⠀⣿⣿⣧⣤⣤⣤⣤⣤⣤⡀⠀⣀⠀⠀⣀⠀⢀⣤⣤⣤⣦⣤⣤⣼⣿⣿⠂⠀⣿⣿⠀⠀⠀
        ⠀⠀⢸⣿⡏⠀⠀⠀⠙⢉⣉⣩⣴⣶⣤⣙⣿⣶⣯⣦⣴⣼⣷⣿⣋⣤⣶⣦⣍⣉⡉⠋⠀⠀⠀⢸⣿⡇⠀⠀
        ⠀⠀⢿⣿⣷⣤⣶⣶⠿⠿⠛⠋⣉⡉⠙⢛⣿⣿⣿⣿⣿⣿⣿⣿⡛⠛⢉⣉⠙⠛⠿⠿⣶⣶⣤⣾⣿⡿⠀⠀
        ⠀⠀⠀⠙⠻⠋⠉⠀⠀⠀⣠⣾⡿⠟⠛⣻⣿⣿⣿⣿⣿⣿⣿⣿⣟⠛⠻⢿⣷⣆⠀⠀⠀⠉⠙⠟⠋⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⢀⣤⣾⠿⠋⢀⣠⣾⠟⢫⣿⣿⣿⣿⣿⣿⡍⠻⣷⣅⡀⠛⠿⣷⣤⡀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⣠⣴⡿⠛⠁⠀⢸⣿⣿⠋⠀⢸⣿⣿⣿⣿⣿⣿⡗⠀⠙⣿⣿⡇⠀⠈⠛⢿⣦⣄⠀⠀⠀⠀⠀
        ⢀⠀⣀⣴⣾⠟⠋⠀⠀⠀⠀⢸⣿⣿⠀⠀⢸⣿⣿⣿⣿⣿⣿⡇⠀⠀⣿⣿⡇⠀⠀⠀⠀⠙⠻⣷⣦⣀⠀⣀
        ⢸⣿⣿⠋⠁⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠈⣿⣿⣿⣿⣿⣿⠁⠀⠐⣿⣿⡇⠀⠀⠀⠀⠀⠀⠈⠙⣿⣿⡟
        ⢸⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⢹⣿⣿⣿⣿⡏⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⡇
        ⢸⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⢿⣿⣿⡿⠀⠀⡈⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⡇
        ⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠈⠿⠿⠁⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀
        ⠀⢻⣿⡄⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠀⠀⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⢀⣿⡟⠀
        ⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠃⠀
        ⠀⠀⠸⣷⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⣿⡟⠀⠀⠀⠄⠀⠀⠀⠀⣾⠏⠀⠀
        ⠀⠀⠀⢻⡆⠀⠀⠀⠀⠀⠀⠀⠸⣿⡄⠀⠀⠀⠀⠀⠀⠄⠀⠀⠀⢀⣿⠇⠀⠀⡂⠀⠀⠀⠀⢰⡟⠀⠀⠀
        ⠀⠀⠀⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⢿⡇⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⢸⡿⠀⠀⠠⠀⠀⠀⠀⠀⡾⠀⠀⠀⠀
        ⠀⠀⠀⠀⠈⢧⠀⠀⠀⠀⠀⠀⠀⠸⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠇⠀⠀⠂⠀⠀⠀⠀⡸⠁⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠀⠀⠄⠀⣠⠄⠀⠀⠁⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⡞⠀⠀⢀⡂⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠜⠀⠀⢁⠅⠀⠀⠀
"""
        yield Static(spider, id="splash-logo")
        yield Static("🕸  SPIDY AI  🕷", id="splash-title")
        yield Static("Initializing modules...", id="splash-text")

    def on_mount(self) -> None:
        self.set_timer(2.0, self.app.pop_screen)


class SessionScreen(Screen):
    BINDINGS = [
        Binding("ctrl+c", "request_quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+t", "toggle_tts", "TTS"),
        Binding("ctrl+v", "toggle_voice", "Voice"),
        Binding("ctrl+p", "command_palette", "Command"),
        Binding("f1", "help", "Help"),
        Binding("ctrl+j", "nav_down", "Down", show=False),
        Binding("ctrl+k", "nav_up", "Up", show=False),
        Binding("ctrl+home", "nav_top", "Top", show=False),
        Binding("ctrl+end", "nav_bottom", "Bottom", show=False),
        Binding("ctrl+r", "toggle_thinking", "Think", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_tokens = 55797

    def compose(self) -> ComposeResult:
        yield SpidyHeader()
        with Horizontal():
            with Container(id="main-area"):
                yield ChatView(id="chat-view")
                yield SpidyPrompt(id="prompt-bar")
                yield QuickCommands(id="quick-commands")
            yield SpidySidebar(id="sidebar")
        yield SpidyFooter()

    def on_mount(self) -> None:
        self.check_sidebar_visibility()
        backend.on_vad_state_change = self.on_vad_changed
        backend.on_wake_word_state_change = self.on_wake_word_changed
        backend.on_token_speed_change = self._on_speed_changed
        asyncio.create_task(self._check_ollama())

    async def _check_ollama(self) -> None:
        ok = await backend.check_connection()
        if not ok:
            self.app.notify(
                "Ollama not reachable — check if it's running", severity="warning"
            )

    def _on_speed_changed(self, speed: float) -> None:
        pass

    def on_screen_resume(self) -> None:
        try:
            inp = self.query_one("#prompt-input")
            inp.focus()
        except Exception:
            pass

    def on_resize(self, event) -> None:
        self.check_sidebar_visibility()

    def check_sidebar_visibility(self) -> None:
        sidebar = self.query_one(SpidySidebar)
        if self.app.size.width < 100:
            sidebar.add_class("hidden")
        else:
            sidebar.remove_class("hidden")

    def update_token_metrics(self, new_tokens: int) -> None:
        self.total_tokens += new_tokens

    def on_spidy_prompt_submitted(self, message: SpidyPrompt.Submitted) -> None:
        text = message.text
        if text.startswith("/"):
            self.handle_command(text)
            return
        chat_view = self.query_one(ChatView)
        chat_view.add_user_message(text)
        asyncio.create_task(self.stream_response(text))

    def on_quick_command_item_clicked(self, message: QuickCommandItem.Clicked) -> None:
        self.handle_command(message.cmd)

    def handle_command(self, cmd: str) -> None:
        parts = cmd.split(" ", 1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        chat_view = self.query_one(ChatView)

        if action == "/clear":
            chat_view.clear_messages()
            backend.clear_conversation()
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
            self.app.theme = (
                "textual-light" if self.app.theme == "textual-dark" else "textual-dark"
            )
            label = "Light" if self.app.theme == "textual-light" else "Dark"
            self.app.notify(f"Theme: {label}")
        elif action == "/check":
            chat_view.add_user_message("/check")
            asyncio.create_task(self.run_system_check_log())
        elif action == "/summarize":
            chat_view.add_user_message("/summarize")
            asyncio.create_task(self.run_summarize_log())
        elif action == "/help":
            self.action_help()
        else:
            self.app.notify(f"Unknown command: {action}")

    async def run_system_check_log(self) -> None:
        chat_view = self.query_one(ChatView)
        chat_view.start_assistant_message()
        chat_view.append_assistant_token("Processing your request...\n")
        await asyncio.sleep(0.5)

        # Simulate diagnostics
        chat_view.start_skill("code_executor")
        await asyncio.sleep(0.8)
        chat_view.end_skill("code_executor", "DONE")

        chat_view.start_skill("search")
        await asyncio.sleep(0.8)
        chat_view.end_skill("search", "DONE")

        chat_view.start_skill("clipboard")
        await asyncio.sleep(0.8)
        chat_view.end_skill("clipboard", "PENDING")

        chat_view.append_assistant_token("\nSystem diagnostics sequence finished.")
        chat_view.end_assistant_message()

    async def run_summarize_log(self) -> None:
        chat_view = self.query_one(ChatView)
        chat_view.start_assistant_message()
        chat_view.append_assistant_token("Summarizing current session context...")
        await asyncio.sleep(1.0)
        chat_view.append_assistant_token(
            f"\nSession summary:\n- Active context: {self.total_tokens} tokens\n- Active branch: main\n- Diagnostics check nominal."
        )
        chat_view.end_assistant_message()

    async def stream_response(self, prompt: str) -> None:
        chat_view = self.query_one(ChatView)
        chat_view.start_assistant_message()
        start_time = time.perf_counter()

        token_count = 0
        async for chunk in backend.stream_chat_response(prompt):
            ctype = chunk["type"]
            if ctype == "message_start":
                pass
            elif ctype == "message_token":
                chat_view.append_assistant_token(chunk["content"])
                token_count += 1
                if token_count % 5 == 0:
                    self.update_token_metrics(5)
            elif ctype == "error":
                chat_view.append_assistant_token(f"\n[error] {chunk['content']}")
            elif ctype == "message_end":
                elapsed = time.perf_counter() - start_time
                if chat_view.current_message:
                    chat_view.current_message.generation_time = elapsed
                chat_view.end_assistant_message()
            elif ctype == "thinking_start":
                chat_view.start_thinking()
            elif ctype == "thinking_token":
                chat_view.append_thinking_token(chunk["content"])
                token_count += 1
                if token_count % 5 == 0:
                    self.update_token_metrics(5)
            elif ctype == "thinking_end":
                chat_view.end_thinking()
            elif ctype == "skill_start":
                chat_view.start_skill(chunk["skill_name"])
            elif ctype == "skill_end":
                chat_view.add_skill_call(chunk["skill_name"], chunk.get("result", ""))
                chat_view.end_skill(chunk["skill_name"], chunk.get("result", ""))

        rem = token_count % 5
        if rem > 0:
            self.update_token_metrics(rem)

    def on_vad_changed(self, state: str) -> None:
        pass

    def on_wake_word_changed(self, state: bool) -> None:
        label = "Microphone Armed" if state else "Microphone Disarmed"
        self.app.notify(label)

    def action_request_quit(self) -> None:
        def check_quit(quit: bool | None) -> None:
            if quit:
                self.app.exit()

        self.app.push_screen(ExitDialog(), check_quit)

    def action_clear_chat(self) -> None:
        self.query_one(ChatView).clear_messages()
        backend.clear_conversation()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(SpidySidebar)
        sidebar.toggle_class("hidden")

    def action_toggle_tts(self) -> None:
        backend.tts_enabled = not backend.tts_enabled
        self.app.notify("TTS On" if backend.tts_enabled else "TTS Off")

    def action_toggle_voice(self) -> None:
        asyncio.create_task(backend.toggle_wake_word())

    def action_command_palette(self) -> None:
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
    CSS_PATH = "app.tcss"
    TITLE = "SPIDY AI"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = ThemeManager()

    def on_mount(self) -> None:
        try:
            self._apply_dynamic_theme()
            self.theme_manager.on_change(self._on_theme_changed)
            asyncio.create_task(self.theme_manager.start_watching())
        except Exception:
            pass

        self.push_screen(SessionScreen())
        self.push_screen(SplashScreen())
        self.set_timer(1.5, self._dismiss_splash)

    async def _dismiss_splash(self) -> None:
        await self.pop_screen()
        try:
            inp = self.screen.query_one("#prompt-input")
            inp.focus()
        except Exception:
            pass

    def _apply_dynamic_theme(self) -> None:
        from textual.theme import Theme

        colors: SpidyThemeColors = self.theme_manager.detect()
        user_text = colors.foreground
        try:
            primary_rgb = _parse_hex(colors.primary)
            if primary_rgb:
                user_text = _best_text_color(primary_rgb)
        except Exception:
            pass

        textual_theme = Theme(
            name="spidy-dynamic",
            primary=colors.primary,
            accent=colors.accent,
            foreground=colors.foreground,
            background=colors.background,
            surface=colors.surface,
            panel=colors.panel,
            success=colors.success,
            error=colors.error,
            warning=colors.warning,
            dark=True,
            variables={
                **colors.to_textual_theme_variables(),
                "--spidy-user-text": user_text,
            },
        )

        try:
            self.unregister_theme("spidy-dynamic")
        except Exception:
            pass
        self.register_theme(textual_theme)
        self.theme = "spidy-dynamic"
        self.refresh_css()

    def _on_theme_changed(self, colors) -> None:
        self.call_from_thread(self._apply_dynamic_theme)


if __name__ == "__main__":
    app = SpidyTUIApp()
    app.run()
