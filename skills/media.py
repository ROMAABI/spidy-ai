import subprocess
import os
from skills.base_skill import BaseSkill

class MediaSkill(BaseSkill):
    name        = "media"
    description = "Play video and audio files or YouTube"
    triggers    = [
        "play", "pause", "stop", "music", "video", "song",
        "youtube", "பாடல்", "வீடியோ", "போடு", "play pannு"
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        if "youtube" in text_lower:
            return self._play_youtube(text_lower)

        if any(w in text_lower for w in ["pause", "stop"]):
            return self._pause()

        return self._play_file(text_lower)

    def _play_youtube(self, text: str) -> dict:
        # Extract search query — remove trigger words
        query = text
        for w in ["play", "youtube", "போடு", "play pannு", "on youtube"]:
            query = query.replace(w, "").strip()

        if not query:
            return {
                "success" : False,
                "speak_en": "What should I play on YouTube?",
                "speak_ta": "YouTube-ல என்ன போடட்டும் அண்ணா?"
            }

        subprocess.Popen(
            ["mpv", f"ytdl://ytsearch:{query}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {
            "success" : True,
            "speak_en": f"Playing {query} on YouTube.",
            "speak_ta": f"{query} YouTube-ல போடுறேன் அண்ணா."
        }

    def _play_file(self, text: str) -> dict:
        # Try to find a file mentioned in the text
        words = text.split()
        for word in words:
            if os.path.exists(word):
                subprocess.Popen(
                    ["mpv", word],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return {
                    "success" : True,
                    "speak_en": f"Playing {word}.",
                    "speak_ta": f"{word} போடுறேன் அண்ணா."
                }

        return {
            "success" : False,
            "speak_en": "I couldn't find a file to play. Give me a file path or say YouTube.",
            "speak_ta": "பாடல் கிடைக்கல அண்ணா. file path சொல்லு அல்லது YouTube சொல்லு."
        }

    def _pause(self) -> dict:
        subprocess.run(["pkill", "-STOP", "mpv"], capture_output=True)
        return {
            "success" : True,
            "speak_en": "Paused.",
            "speak_ta": "நிறுத்தினேன் அண்ணா."
        }