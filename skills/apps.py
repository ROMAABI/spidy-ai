import os
import signal
import subprocess
import time
from difflib import get_close_matches
from skills.base_skill import BaseSkill

LAST_OPENED = None
SPIDY_PROCESSES = []

DISPLAY_NAMES = {
    "firefox": "Firefox",
    "google-chrome": "Chrome",
    "chrome": "Chrome",
    "chromium": "Chromium",
    "brave": "Brave",
    "code": "VS Code",
    "vscode": "VS Code",
    "opencode": "OpenCode",
    "nvim": "Neovim",
    "vim": "Vim",
    "kitty": "Terminal",
    "alacritty": "Terminal",
    "spotify": "Spotify",
    "telegram": "Telegram",
    "discord": "Discord",
    "nautilus": "Files",
    "thunar": "Files",
    "dolphin": "Files",
    "python": "Python",
    "python3": "Python",
    "node": "Node",
}

BINARY_MAP = {
    "nvim": "nvim",
    "vim": "vim",
    "code": "code",
    "vscode": "code",
    "opencode": "opencode",
    "python": "python",
    "python3": "python",
    "node": "node",
    "npm": "npm",
    "git": "git",
    "htop": "htop",
    "btop": "btop",
    "ranger": "ranger",
}

APP_ALIASES = {
    "browser": ["firefox", "chrome", "chromium", "brave"],
    "editor": ["code", "nvim", "vim"],
    "terminal": ["kitty", "alacritty"],
    "music": ["spotify"],
    "files": ["nautilus", "thunar", "dolphin"],
    "chat": ["telegram", "discord"],
}

SYSTEM_APPS = None


def is_hyprland():
    """Check if running in Hyprland."""
    return os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")


def get_display_name(app):
    """Get clean display name for app."""
    app = app.lower().split("/")[-1]
    return DISPLAY_NAMES.get(app, app.capitalize())


def get_clean_name(full_path):
    """Extract clean binary name from path."""
    if not full_path:
        return None
    name = full_path.strip().split()[-1].split("/")[-1]
    return name.split("-")[-1]


def get_binary(cmd):
    """Check if command exists in PATH."""
    return (
        subprocess.call(
            ["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        == 0
    )


def scan_apps():
    global SYSTEM_APPS
    paths = [
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/applications"),
    ]

    apps = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for file in os.listdir(path):
            if not file.endswith(".desktop"):
                continue
            full_path = os.path.join(path, file)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                name, exec_cmd = None, None
                for line in lines:
                    if line.startswith("Name=") and not name:
                        name = line.split("=", 1)[1].strip().lower()
                    elif line.startswith("Exec=") and not exec_cmd:
                        exec_cmd = line.split("=", 1)[1].strip()
                        exec_cmd = exec_cmd.replace("%u", "").replace("%U", "")
                        exec_cmd = exec_cmd.replace("%f", "").replace("%F", "")
                        exec_cmd = exec_cmd.split()[0]
                if name and exec_cmd:
                    apps[name] = exec_cmd
            except:
                continue
    SYSTEM_APPS = apps
    return apps


def resolve_app(user_input):
    global LAST_OPENED
    if SYSTEM_APPS is None:
        scan_apps()
    user_input = user_input.lower()

    for cmd in sorted(BINARY_MAP.keys(), key=len, reverse=True):
        if cmd in user_input and get_binary(BINARY_MAP[cmd]):
            return BINARY_MAP[cmd]

    for category, apps in APP_ALIASES.items():
        if category in user_input:
            return apps[0]

    for name, cmd in SYSTEM_APPS.items():
        if name in user_input:
            return cmd

    match = get_close_matches(user_input, SYSTEM_APPS.keys(), n=1, cutoff=0.6)
    if match:
        return SYSTEM_APPS[match[0]]
    return None


def find_process_by_name(name):
    """Find process entry by app name."""
    name = get_clean_name(name) or name.lower()
    for entry in SPIDY_PROCESSES:
        entry_name = get_clean_name(entry.get("app", ""))
        if entry_name and (name in entry_name or entry_name in name):
            return entry
    return None


def close_by_pid(pid, name):
    """Close process by PID with proper signal handling."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return True
    except ProcessLookupError:
        return True
    except Exception:
        return False


def close_by_hyprland():
    """Close active window using Hyprland."""
    if not is_hyprland():
        return False
    try:
        subprocess.run(
            ["hyprctl", "dispatch", "killactive"], capture_output=True, timeout=2
        )
        return True
    except:
        return False


class AppsSkill(BaseSkill):
    name = "apps"
    description = "Open and close applications"
    triggers = [
        "open",
        "launch",
        "start",
        "close",
        "kill",
        "thirak",
        "muodu",
        "force",
        "firefox",
        "chrome",
        "terminal",
        "kitty",
        "code",
        "vscode",
        "telegram",
        "spotify",
        "files",
        "nautilus",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()
        if any(w in text_lower for w in ["close", "kill", "muodu", "close pannu"]):
            return self._close_app(text_lower)
        return self._open_app(text_lower)

    def _open_app(self, text: str) -> dict:
        global LAST_OPENED, SPIDY_PROCESSES

        app = resolve_app(text)
        if not app:
            return {
                "success": False,
                "speak_en": "Which app should I open?",
                "speak_ta": "Enna app திறக்க வேணும்?",
            }

        try:
            env = os.environ.copy()
            env["DISPLAY"] = env.get("DISPLAY", ":1")
            if env.get("XAUTHORITY"):
                env["XAUTHORITY"] = env["XAUTHORITY"]

            proc = subprocess.Popen(
                app.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
            )

            clean_name = get_clean_name(app)
            entry = {"app": app, "pid": proc.pid, "name": clean_name}
            SPIDY_PROCESSES.append(entry)
            LAST_OPENED = entry

            return {
                "success": True,
                "speak_en": f"Opening {get_display_name(app)}",
                "speak_ta": f"{get_display_name(app)} திறக்கிறேன்!",
            }
        except Exception as e:
            return {
                "success": False,
                "speak_en": f"Failed to open {get_display_name(app)}",
                "speak_ta": f"{get_display_name(app)} திறக்க முடியல",
            }

    def _close_app(self, text: str) -> dict:
        global LAST_OPENED, SPIDY_PROCESSES

        user_input = text.lower()

        target_entry = None
        is_force = "force" in user_input or "kill" in user_input
        is_close_all = False

        if "it" in user_input:
            if LAST_OPENED:
                target_entry = LAST_OPENED
            else:
                display_name = "None"
                return {
                    "success": False,
                    "speak_en": "No recent app to close",
                    "speak_ta": "முந்திய app இல்ல",
                }
        else:
            app = resolve_app(user_input)
            if not app:
                display_name = "None"
                return {
                    "speak_en": "Which app should I close?",
                    "speak_ta": "Enna app மூட வேணும்?",
                }

            target_entry = find_process_by_name(app)

            if not target_entry and is_force:
                is_close_all = True
                target_entry = {"app": app, "name": get_clean_name(app)}

        if not target_entry:
            display_name = get_display_name(
                target_entry.get("app", app) if target_entry else app
            )
            if is_force:
                return {
                    "success": False,
                    "speak_en": f"{display_name} is not opened by me. Close all?",
                    "speak_ta": f"நான் {display_name} திறக்கல",
                }
            return {
                "success": False,
                "speak_en": f"I didn't open {display_name}",
                "speak_ta": f"நான் {display_name} திறக்கல",
            }

        app_name = target_entry.get("name", get_clean_name(target_entry.get("app", "")))
        display_name = get_display_name(target_entry.get("app", app_name))
        target_pid = target_entry.get("pid")

        if is_close_all:
            try:
                import subprocess as sp

                result = sp.run(["pkill", "-f", app_name], capture_output=True)
                if result.returncode == 0:
                    SPIDY_PROCESSES = []
                    LAST_OPENED = None
                    return {
                        "success": True,
                        "speak_en": f"Closed all {display_name} instances",
                        "speak_ta": f"அனிவு {display_name} மூடினேன்",
                    }
            except:
                pass
            return {
                "success": False,
                "speak_en": f"Could not close {display_name}",
                "speak_ta": f"{display_name} மூட முடியல",
            }

        if target_pid:
            if close_by_pid(target_pid, app_name):
                SPIDY_PROCESSES = [
                    e for e in SPIDY_PROCESSES if e.get("pid") != target_pid
                ]
                if LAST_OPENED and LAST_OPENED.get("pid") == target_pid:
                    LAST_OPENED = None
                return {
                    "success": True,
                    "speak_en": f"Closed {display_name}",
                    "speak_ta": f"{display_name} மூடினேன்",
                }

        if is_hyprland():
            if close_by_hyprland():
                return {
                    "success": True,
                    "speak_en": f"Closed {display_name}",
                    "speak_ta": f"{display_name} மூடினேன்",
                }

        if is_force:
            try:
                import subprocess as sp

                sp.run(["pkill", "-f", app_name], capture_output=True)
                SPIDY_PROCESSES = []
                LAST_OPENED = None
                return {
                    "success": True,
                    "speak_en": f"Force closed {display_name}",
                    "speak_ta": f"{display_name} மூடினேன்",
                }
            except:
                pass

        return {
            "success": False,
            "speak_en": f"Could not close {display_name}",
            "speak_ta": f"{display_name} மூட முடியல",
        }
