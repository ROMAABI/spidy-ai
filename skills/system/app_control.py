import os
import subprocess
import time
from difflib import get_close_matches
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

SITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "gmail": "https://mail.google.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "spotify": "https://open.spotify.com",
    "discord": "https://discord.com/app",
    "telegram": "https://web.telegram.org",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "maps": "https://maps.google.com",
    "weather": "https://weather.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "arch wiki": "https://wiki.archlinux.org",
    "archlinux": "https://wiki.archlinux.org",
    "hyprland": "https://wiki.hyprland.org",
    "hyprland docs": "https://wiki.hyprland.org",
    "hyprland wiki": "https://wiki.hyprland.org",
    "localhost": "http://localhost",
    "localhost:3000": "http://localhost:3000",
    "localhost:8000": "http://localhost:8000",
}

DISPLAY_NAMES = {
    "firefox": "Firefox",
    "google-chrome": "Chrome",
    "chrome": "Chrome",
    "chromium": "Chromium",
    "code": "VS Code",
    "vscode": "VS Code",
    "kitty": "Terminal",
    "alacritty": "Terminal",
    "spotify": "Spotify",
    "thunar": "File Manager",
    "nautilus": "File Manager",
    "dolphin": "File Manager",
    "steam": "Steam",
    "obs": "OBS Studio",
    "vlc": "VLC",
    "mpv": "MPV",
    "libreoffice": "LibreOffice",
    "calculator": "Calculator",
    "calendar": "Calendar",
    "settings": "Settings",
}

APP_ALIASES = {
    "browser": "firefox",
    "editor": "code",
    "terminal": "kitty",
    "files": "dolphin",
    "file manager": "dolphin",
    "home": os.path.expanduser("~"),
    "home folder": os.path.expanduser("~"),
    "downloads": os.path.expanduser("~/Downloads"),
    "current project": str(Path.cwd()),
}

BROWSER_CANDIDATES = ["firefox", "google-chrome", "chromium", "brave-browser", "microsoft-edge"]


def _find_browser() -> str:
    for b in BROWSER_CANDIDATES:
        if subprocess.run(["which", b], capture_output=True).returncode == 0:
            return b
    return "xdg-open"


def _open_url(url: str) -> dict:
    browser = _find_browser()
    try:
        proc = subprocess.Popen(
            [browser, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.3)
        if proc.poll() is not None and proc.returncode != 0:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": url, "command": f"{browser} {url}", "action": "open"}
    except FileNotFoundError:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": url, "command": f"xdg-open {url}", "action": "open"}


def _open_app(app: str) -> dict:
    if app in APP_ALIASES:
        app = APP_ALIASES[app]
    if os.path.isdir(app):
        subprocess.Popen(["dolphin", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": app, "command": f"dolphin {app}", "action": "open"}
    executable = subprocess.run(["which", app], capture_output=True, text=True)
    if executable.returncode == 0:
        path = executable.stdout.strip()
        subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": app, "command": path, "action": "open"}
    desktop_files = list(Path("/usr/share/applications").glob(f"*{app}*.desktop"))
    if not desktop_files:
        desktop_files = list(Path.home().joinpath(".local/share/applications").glob(f"*{app}*.desktop"))
    if desktop_files:
        subprocess.Popen(["gtk-launch", desktop_files[0].stem], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": app, "command": f"gtk-launch {desktop_files[0].stem}", "action": "open"}
    try:
        subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": app, "command": app, "action": "open"}
    except FileNotFoundError:
        return {"success": False, "output": f"{app} not found", "command": app, "action": "open"}


def _search_url(engine: str, query: str) -> dict:
    engines = {
        "google": f"https://www.google.com/search?q={query}",
        "youtube": f"https://www.youtube.com/results?search_query={query}",
        "github": f"https://github.com/search?q={query}",
    }
    url = engines.get(engine, f"https://www.google.com/search?q={query}")
    return _open_url(url)


def _classify_intent(text: str) -> tuple[str, float]:
    text_lower = text.lower().strip()
    words = text_lower.split()

    question_starters = ["what", "who", "where", "when", "why", "how", "which",
                         "is", "are", "was", "were", "can", "could", "would",
                         "should", "do", "does", "did"]
    info_phrases = ["tell me about", "explain", "describe", "what is", "what are",
                    "what does", "how does", "how do", "do you know", "know about",
                    "what's", "who is", "who are"]
    chat_words = ["hi", "hello", "hey", "thanks", "thank", "bye", "goodbye",
                  "nice", "cool", "awesome", "great", "ok", "okay", "yes", "no",
                  "how are you", "what's up", "sup"]

    for phrase in info_phrases:
        if phrase in text_lower:
            return "QUESTION", 0.95
    if words and words[0] in question_starters:
        return "QUESTION", 0.90
    if text_lower.endswith("?"):
        return "QUESTION", 0.85

    for phrase in chat_words:
        if text_lower == phrase or text_lower.startswith(phrase):
            return "CHAT", 0.90

    search_match = False
    for engine in ["google", "youtube", "github"]:
        if f"search {engine} for" in text_lower:
            search_match = True
            break
    if text_lower.startswith("search ") or text_lower.startswith("find "):
        search_match = True
    if search_match:
        return "SEARCH", 0.90

    command_starters = ["open", "launch", "start", "close", "kill", "shut",
                        "run", "execute", "toggle", "switch to", "focus",
                        "play", "show", "increase", "decrease", "set",
                        "turn", "mute", "unmute", "search", "find"]
    for starter in command_starters:
        if text_lower.startswith(starter + " ") or text_lower == starter:
            return "COMMAND", 0.90

    return "CHAT", 0.50


def _parse_open_command(text: str) -> dict:
    text_lower = text.lower().strip()
    close_words = ["close", "kill", "muodu", "po"]
    words = text_lower.split()
    if any(w in words for w in close_words):
        app = text_lower
        for w in close_words + ["the", "app", "application", "pannu"]:
            app = app.replace(w, "").strip()
        if app:
            subprocess.run(["pkill", "-f", app], capture_output=True)
            return {"success": True, "output": app, "command": f"pkill -f {app}", "action": "close"}
    search_match = None
    for engine in ["google", "youtube", "github"]:
        pattern = f"search {engine} for "
        if pattern in text_lower:
            query = text_lower.split(pattern, 1)[1].strip()
            search_match = (engine, query)
            break
    if search_match:
        return _search_url(search_match[0], search_match[1])
    words_to_remove = ["open", "launch", "start", "thira", "thirakku"]
    app = text_lower
    for w in words_to_remove:
        if app.startswith(w + " "):
            app = app[len(w):].strip()
            break
    if not app:
        return {"success": False, "output": "No app or URL specified", "command": ""}
    if app in SITES:
        return _open_url(SITES[app])
    if app in APP_ALIASES:
        return _open_app(APP_ALIASES[app])
    if app in DISPLAY_NAMES:
        return _open_app(app)
    if os.path.exists(app):
        if os.path.isdir(app):
            return _open_app(app)
        subprocess.Popen(["xdg-open", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "output": app, "command": f"xdg-open {app}", "action": "open"}
    if "." in app and "/" not in app:
        return _open_url(f"https://{app}")
    result = _open_app(app)
    return result


class AppControlSkill(BaseSkill):
    name = "app_control"
    description = "Open, close, or focus an application or website by name"
    triggers = ["open", "launch", "start", "close", "kill", "focus", "switch to"]

    def can_handle(self, text: str) -> bool:
        intent, confidence = _classify_intent(text)
        return intent == "COMMAND" and confidence >= 0.90

    def run(self, text: str, lang: str = "en") -> dict:
        result = _parse_open_command(text)
        if result["action"] == "close":
            return {"success": True, "speak_en": f"Closed {result['output']}.", "speak_ta": f"{result['output']} மூடினேன்."}
        display = DISPLAY_NAMES.get(result["output"], result["output"].capitalize())
        return {"success": True, "speak_en": f"Opening {display}.", "speak_ta": f"{display} திறக்கிறேன்."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "app_name": {"type": "string", "description": "Application or website name to open/close"},
            "action": {"type": "string", "enum": ["open", "close"], "description": "Action to perform"},
        }, "required": ["app_name", "action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"{kwargs['action']} {kwargs['app_name']}")["speak_en"])
