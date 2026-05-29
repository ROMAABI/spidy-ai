"""
skills/clipboard.py  –  Read and write clipboard via wl-clipboard (Wayland).
Falls back to xclip/xsel for X11.
"""
import subprocess
from skills.base_skill import BaseSkill


class ClipboardSkill(BaseSkill):
    name        = "clipboard"
    description = "Read and write the system clipboard"
    triggers    = [
        "clipboard", "copy", "paste", "clip", "copied text",
        "what did i copy", "read clipboard", "clipboard la enna",
        "clipboard paru", "copy pannidu", "paste pannidu",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        # Read clipboard
        if any(w in text_lower for w in [
            "read", "what", "show", "paru", "enna", "என்ன", "paste"
        ]):
            return self._read_clipboard(lang)

        # Copy something — extract quoted content
        import re
        m = re.search(r'["\u201c\u201d](.*?)["\u201c\u201d]', text)
        if m:
            return self._write_clipboard(m.group(1), lang)

        # Default: read
        return self._read_clipboard(lang)

    def _read_clipboard(self, lang: str) -> dict:
        content = self._wl_paste() or self._x_paste()
        if content is None:
            return {
                "success" : False,
                "speak_en": "I couldn't access the clipboard.",
                "speak_ta": "Clipboard access ஆகல அண்ணா.",
            }
        if not content:
            return {
                "success" : True,
                "speak_en": "Your clipboard is empty.",
                "speak_ta": "Clipboard காலியா இருக்கு அண்ணா.",
            }
        preview = content[:150].replace("\n", " ")
        return {
            "success" : True,
            "speak_en": f"Your clipboard contains: {preview}",
            "speak_ta": f"Clipboard ல இருக்கு அண்ணா: {preview}",
        }

    def _write_clipboard(self, content: str, lang: str) -> dict:
        ok = self._wl_copy(content) or self._x_copy(content)
        if ok:
            return {
                "success" : True,
                "speak_en": f"Copied to clipboard: {content[:80]}",
                "speak_ta": f"Clipboard ல copy பண்ணிட்டேன் அண்ணா.",
            }
        return {
            "success" : False,
            "speak_en": "Couldn't write to clipboard.",
            "speak_ta": "Clipboard ல write ஆகல அண்ணா.",
        }

    # ── backend helpers ───────────────────────────────────────────────────────
    def _wl_paste(self) -> str | None:
        try:
            r = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=3)
            return r.stdout if r.returncode == 0 else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def _wl_copy(self, text: str) -> bool:
        try:
            r = subprocess.run(["wl-copy"], input=text, text=True, capture_output=True, timeout=3)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _x_paste(self) -> str | None:
        for cmd in [["xclip", "-o", "-sel", "clip"], ["xsel", "--clipboard", "--output"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if r.returncode == 0:
                    return r.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def _x_copy(self, text: str) -> bool:
        for cmd in [["xclip", "-sel", "clip"], ["xsel", "--clipboard", "--input"]]:
            try:
                r = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=3)
                if r.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False
