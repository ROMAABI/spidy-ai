import asyncio, subprocess
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_MONITORING = False
_KNOWN_FILES = set()

class MonitorDownloadsSkill(BaseSkill):
    name = "monitor_downloads"
    description = "Monitor a download folder and alert on new files"
    triggers = ["monitor downloads", "watch downloads", "download watcher"]

    def run(self, text: str, lang: str = "en") -> dict:
        global _MONITORING, _KNOWN_FILES
        t = text.lower()
        if any(w in t for w in ["stop", "end", "niruthu"]):
            _MONITORING = False
            return {"success": True, "speak_en": "Download monitoring stopped.", "speak_ta": "Monitoring நிறுத்தினேன் அண்ணா."}
        if any(w in t for w in ["start", "begin", "watch"]):
            download_dir = Path.home() / "Downloads"
            _KNOWN_FILES = set(download_dir.iterdir()) if download_dir.exists() else set()
            _MONITORING = True
            asyncio.create_task(self._watch_loop(download_dir))
            return {"success": True, "speak_en": f"Monitoring {download_dir}.", "speak_ta": "Download folder watch பண்றேன் அண்ணா."}
        return {"success": False, "speak_en": "Say monitor start or stop.", "speak_ta": "Monitor start/stop சொல்லுங்க."}

    async def _watch_loop(self, directory: Path):
        global _KNOWN_FILES
        while _MONITORING:
            await asyncio.sleep(5)
            current = set(directory.iterdir()) if directory.exists() else set()
            new = current - _KNOWN_FILES
            for f in new:
                subprocess.run(["notify-send", "New Download", str(f.name)])
            _KNOWN_FILES = current

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["start", "stop"], "description": "Monitoring action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"{kwargs.get('action', 'start')} monitor downloads")["speak_en"])
