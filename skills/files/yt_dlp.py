import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class YtDlpSkill(BaseSkill):
    name = "yt_dlp"
    description = "Download video/audio from URL using yt-dlp"
    triggers = ["download video", "download audio", "yt-dlp", "youtube download", "save video"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["download video", "download audio", "youtube download", "save video", "download"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "Provide a URL to download.", "speak_ta": "URL சொல்லுங்க அண்ணா."}
        url = t.split()[0]
        dest = Path.home() / "Downloads"
        audio = any(w in text.lower() for w in ["audio", "mp3", "music", "song"])
        try:
            cmd = ["yt-dlp"]
            if audio:
                cmd += ["-x", "--audio-format", "mp3"]
            cmd += ["-P", str(dest), url]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            fmt = "audio" if audio else "video"
            return {"success": True, "speak_en": f"Downloading {fmt} to {dest}.", "speak_ta": f"{fmt} download பண்ணுறேன் அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Download error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "url": {"type": "string", "description": "Video URL to download"},
            "format": {"type": "string", "enum": ["video", "audio"], "description": "Download format"},
        }, "required": ["url"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"download {kwargs.get('url', '')} {kwargs.get('format', 'video')}")["speak_en"])
