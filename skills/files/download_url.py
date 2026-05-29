import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class DownloadUrlSkill(BaseSkill):
    name = "download_url"
    description = "Download a file from a URL using wget or curl"
    triggers = ["download", "download file", "wget", "curl", "get file", "download pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["download file", "download pannu", "download", "get file"]:
            t = t.replace(w, "").strip()
        if not t or "http" not in t:
            return {"success": False, "speak_en": "Provide a URL to download.", "speak_ta": "URL சொல்லுங்க அண்ணா."}
        url = t.split()[0]
        dest = Path.home() / "Downloads"
        dest.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["wget", url, "-P", str(dest)], check=True, timeout=120)
            return {"success": True, "speak_en": f"Downloaded to {dest}.", "speak_ta": f"Download பண்ணேன் {dest} க்கு அண்ணா."}
        except subprocess.TimeoutExpired:
            return {"success": False, "speak_en": "Download timed out.", "speak_ta": "Download timeout அண்ணா."}
        except FileNotFoundError:
            try:
                subprocess.run(["curl", "-O", url], cwd=dest, check=True, timeout=120)
                return {"success": True, "speak_en": f"Downloaded to {dest}.", "speak_ta": "Download பண்ணேன் அண்ணா."}
            except Exception as e:
                return {"success": False, "speak_en": f"Download failed: {e}", "speak_ta": "Download fail அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL to download"},
            "destination": {"type": "string", "description": "Save directory (default: ~/Downloads)"},
        }, "required": ["url"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"download {kwargs.get('url', '')}")["speak_en"])
