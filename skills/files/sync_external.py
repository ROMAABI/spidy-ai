import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class SyncExternalSkill(BaseSkill):
    name = "sync_external"
    description = "Sync a folder to an external drive using rsync"
    triggers = ["sync", "external drive", "backup drive", "rsync", "sync to usb"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["sync to", "sync", "external drive", "backup drive", "backup to"]:
            t = t.replace(w, "").strip()
        words = t.split()
        if len(words) < 2:
            return {"success": False, "speak_en": "Usage: sync <source> <destination>", "speak_ta": "Sync format: sync <source> <destination>"}
        src = Path(words[0]).expanduser()
        dst = Path(words[1]).expanduser()
        if not src.exists():
            return {"success": False, "speak_en": f"Source not found: {src}", "speak_ta": "Source கிடைக்கல அண்ணா."}
        if not dst.exists():
            dst.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["rsync", "-avh", "--progress", str(src) + "/", str(dst) + "/"],
                check=True, timeout=300,
            )
            return {"success": True, "speak_en": f"Synced {src.name} to {dst.name}.", "speak_ta": "Sync முடிந்தது அண்ணா."}
        except subprocess.TimeoutExpired:
            return {"success": False, "speak_en": "Sync timed out.", "speak_ta": "Sync timeout அண்ணா."}
        except FileNotFoundError:
            return {"success": False, "speak_en": "Install rsync: sudo pacman -S rsync", "speak_ta": "rsync install பண்ணுங்க அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Sync error: {e}", "speak_ta": "Sync error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "source": {"type": "string", "description": "Source directory path"},
            "destination": {"type": "string", "description": "Destination directory path"},
        }, "required": ["source", "destination"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"sync {kwargs.get('source', '')} {kwargs.get('destination', '')}")["speak_en"])
