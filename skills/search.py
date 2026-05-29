import subprocess
from skills.base_skill import BaseSkill

class SearchSkill(BaseSkill):
    name        = "search"
    description = "Web search — opens browser with query"
    triggers    = [
        "search", "google", "look up", "find", "தேடு",
        "browse", "open website", "search for",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        query = text
        for w in ["search for", "search", "google", "look up", "find", "தேடு", "browse", "for"]:
            query = query.replace(w, "").strip()

        if not query:
            return {
                "success" : False,
                "speak_en": "What should I search for?",
                "speak_ta": "என்ன தேடட்டும் அண்ணா?"
            }

        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {
            "success" : True,
            "speak_en": f"Searching for {query}.",
            "speak_ta": f"{query} தேடுறேன் அண்ணா."
        }