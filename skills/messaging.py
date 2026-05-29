import subprocess
from skills.base_skill import BaseSkill

class MessagingSkill(BaseSkill):
    name        = "messaging"
    description = "Open messaging apps"
    triggers    = [
        "whatsapp", "telegram", "message", "chat",
        "send message", "சேட்", "மெசேஜ்"
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        if "whatsapp" in text_lower:
            subprocess.Popen(
                ["xdg-open", "https://web.whatsapp.com"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "success" : True,
                "speak_en": "Opening WhatsApp Web.",
                "speak_ta": "WhatsApp திறக்கிறேன் அண்ணா."
            }

        if "telegram" in text_lower:
            subprocess.Popen(
                ["telegram-desktop"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "success" : True,
                "speak_en": "Opening Telegram.",
                "speak_ta": "Telegram திறக்கிறேன் அண்ணா."
            }

        return {
            "success" : False,
            "speak_en": "Which app do you want to message on?",
            "speak_ta": "எந்த app-ல message அனுப்பட்டும் அண்ணா?"
        }