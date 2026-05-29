"""
skills/hyprland.py  –  Hyprland window manager control via hyprctl.
"""
import subprocess
import json
from skills.base_skill import BaseSkill


class HyprlandSkill(BaseSkill):
    name        = "hyprland"
    description = "Control the Hyprland window manager — switch workspaces, move windows, etc."
    triggers    = [
        "workspace", "switch workspace", "move to workspace", "go to workspace",
        "focus window", "move window", "fullscreen", "float", "tile",
        "hyprland", "hypr", "window", "monitor",
        "workspace la po", "workspace switch pannு",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        # Switch workspace
        ws = self._extract_number(text_lower)

        if any(w in text_lower for w in ["workspace", "switch", "go to", "po"]):
            if ws:
                return self._switch_workspace(ws, lang)

        if "fullscreen" in text_lower:
            return self._dispatch("fullscreen", lang)

        if "float" in text_lower:
            return self._dispatch("togglefloating", lang)

        if "tile" in text_lower:
            return self._dispatch("togglefloating", lang)  # toggle back

        if any(w in text_lower for w in ["close window", "kill window", "window close"]):
            return self._dispatch("killactive", lang)

        if "next workspace" in text_lower or "next window" in text_lower:
            return self._dispatch("workspace e+1", lang)

        if "prev workspace" in text_lower or "previous workspace" in text_lower:
            return self._dispatch("workspace e-1", lang)

        if "clients" in text_lower or "windows" in text_lower or "list" in text_lower:
            return self._list_clients(lang)

        return {
            "success" : False,
            "speak_en": "I didn't understand the Hyprland command. Try: switch workspace 2, fullscreen, or float.",
            "speak_ta": "Hyprland command புரியல அண்ணா. 'workspace 2', 'fullscreen' சொல்லுங்க.",
        }

    # ── actions ───────────────────────────────────────────────────────────────
    def _switch_workspace(self, num: int, lang: str) -> dict:
        self._hyprctl(f"dispatch workspace {num}")
        return {
            "success" : True,
            "speak_en": f"Switched to workspace {num}.",
            "speak_ta": f"Workspace {num} க்கு போனோம் அண்ணா.",
        }

    def _dispatch(self, cmd: str, lang: str) -> dict:
        self._hyprctl(f"dispatch {cmd}")
        return {
            "success" : True,
            "speak_en": f"Done: {cmd}.",
            "speak_ta": f"Done அண்ணா: {cmd}.",
        }

    def _list_clients(self, lang: str) -> dict:
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=3
            )
            clients = json.loads(result.stdout or "[]")
            titles = [c.get("title", "Unknown") for c in clients[:5]]
            summary = ", ".join(titles) if titles else "No windows open."
            return {
                "success" : True,
                "speak_en": f"Open windows: {summary}",
                "speak_ta": f"திறந்த windows: {summary}",
            }
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": f"Error: {e}"}

    # ── helpers ───────────────────────────────────────────────────────────────
    def _hyprctl(self, cmd: str):
        try:
            subprocess.run(["hyprctl", *cmd.split()], capture_output=True, timeout=3)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _extract_number(self, text: str) -> int | None:
        import re
        m = re.search(r"\b(\d+)\b", text)
        return int(m.group(1)) if m else None
