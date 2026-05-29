import re, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_PATTERNS = [
    re.compile(r"\[.*?\]\s*(.+?)\s*-\s*(\d+)", re.I),
    re.compile(r"(.+?)[_\s.]*[Ee]p?\s*(\d+)", re.I),
    re.compile(r"(.+?)[_\s.]*(\d{2,3})", re.I),
]

class AnimeRenameSkill(BaseSkill):
    name = "anime_rename"
    description = "Rename anime episode files to proper format (Show Name - EpXX.ext)"
    triggers = ["rename anime", "anime rename", "anime", "episode rename"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["rename anime", "anime rename", "episode rename", "rename"]:
            t = t.replace(w, "").strip()
        directory = Path(t).expanduser() if t else Path.home() / "Downloads"
        if not directory.exists():
            return {"success": False, "speak_en": f"Directory not found: {directory}", "speak_ta": "Directory கிடைக்கல அண்ணா."}
        renamed = 0
        for f in sorted(directory.iterdir()):
            if f.is_file() and f.suffix.lower() in (".mkv", ".mp4", ".avi", ".webm"):
                stem = f.stem
                for pat in _PATTERNS:
                    m = pat.search(stem)
                    if m:
                        show = m.group(1).strip().replace(".", " ").replace("_", " ").title()
                        ep = m.group(2).zfill(2)
                        new_name = f"{show} - Ep{ep}{f.suffix}"
                        new_path = f.parent / new_name
                        if not new_path.exists():
                            f.rename(new_path)
                            renamed += 1
                        break
        if renamed:
            return {"success": True, "speak_en": f"Renamed {renamed} files.", "speak_ta": f"{renamed} files rename பண்ணேன் அண்ணா."}
        return {"success": True, "speak_en": "No anime files to rename.", "speak_ta": "Rename பண்ண files இல்ல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory with anime files (default: ~/Downloads)"},
        }, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("directory", ""))["speak_en"])
