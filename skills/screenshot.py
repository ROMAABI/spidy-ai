"""
skills/screenshot.py  –  Take a screenshot and optionally describe it via LLaVA.
"""
import subprocess
import os
import time
from skills.base_skill import BaseSkill

SCREENSHOT_PATH = "/tmp/spidy_screenshot.png"


class ScreenshotSkill(BaseSkill):
    name        = "screenshot"
    description = "Take a screenshot and optionally describe what's on screen using LLaVA"
    triggers    = [
        "screenshot", "screen shot", "capture screen", "what's on screen",
        "whats on screen", "describe screen", "screen la enna",
        "screen paru", "screen capture",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        # Take screenshot with grim (Wayland) or scrot (X11)
        ok = self._take_screenshot()
        if not ok:
            return {
                "success" : False,
                "speak_en": "I couldn't take a screenshot. Is grim or scrot installed?",
                "speak_ta": "Screenshot எடுக்க முடியல அண்ணா.",
            }

        text_lower = text.lower()
        describe = any(w in text_lower for w in [
            "describe", "what", "enna", "என்ன", "paru", "பாரு", "explain"
        ])

        if describe:
            return self._describe_screenshot(lang)

        return {
            "success" : True,
            "speak_en": f"Screenshot saved to {SCREENSHOT_PATH}.",
            "speak_ta": f"Screenshot எடுத்தாயிட்டேன் அண்ணா.",
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    def _take_screenshot(self) -> bool:
        # Try grim first (Wayland/Hyprland)
        for cmd in [
            ["grim", SCREENSHOT_PATH],
            ["scrot", SCREENSHOT_PATH],
            ["import", "-window", "root", SCREENSHOT_PATH],  # ImageMagick
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and os.path.exists(SCREENSHOT_PATH):
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False

    def _describe_screenshot(self, lang: str) -> dict:
        try:
            result = subprocess.run(
                [
                    "ollama", "run", "llava",
                    f"Describe what you see on this screen briefly: {SCREENSHOT_PATH}",
                ],
                capture_output=True, text=True, timeout=30
            )
            description = result.stdout.strip() or "I can see your screen but couldn't generate a description."
            description = description[:300]
            return {
                "success" : True,
                "speak_en": description,
                "speak_ta": description,
            }
        except FileNotFoundError:
            return {
                "success" : True,
                "speak_en": "Screenshot saved! LLaVA is not installed so I can't describe it.",
                "speak_ta": "Screenshot எடுத்தாயிட்டேன் அண்ணா! LLaVA இல்ல, describe பண்ண முடியல.",
            }
        except subprocess.TimeoutExpired:
            return {
                "success" : True,
                "speak_en": "Screenshot done, but description timed out.",
                "speak_ta": "Screenshot எடுத்தேன் அண்ணா, describe time out ஆச்சு.",
            }
