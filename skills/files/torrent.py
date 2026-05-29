import subprocess, asyncio
from skills.base_skill import BaseSkill, SkillResult

class TorrentSkill(BaseSkill):
    name = "torrent"
    description = "Add a torrent by magnet link or file path using transmission-cli"
    triggers = ["torrent", "add torrent", "magnet", "transmission", "torrent add"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["add torrent", "torrent add", "torrent", "add"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "Provide a magnet link or torrent file.", "speak_ta": "Magnet link or torrent file சொல்லுங்க அண்ணா."}
        link = t.split()[0]
        try:
            if link.startswith("magnet:"):
                subprocess.Popen(["transmission-remote", "-a", link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["transmission-remote", "-a", link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": "Torrent added.", "speak_ta": "Torrent add பண்ணேன் அண்ணா."}
        except FileNotFoundError:
            return {"success": False, "speak_en": "Install: sudo pacman -S transmission-cli", "speak_ta": "transmission-cli install பண்ணுங்க அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Torrent error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "magnet": {"type": "string", "description": "Magnet link or torrent file path"},
        }, "required": ["magnet"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"torrent {kwargs.get('magnet', '')}")["speak_en"])
