import shutil, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_RULES = {
    "Videos": [".mp4", ".mkv", ".webm", ".avi", ".mov"],
    "Music": [".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".odt", ".md", ".csv", ".xlsx", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".sh", ".rs", ".go"],
    "Archives": [".zip", ".tar.gz", ".tgz", ".rar", ".7z"],
}

class AutoSortSkill(BaseSkill):
    name = "auto_sort"
    description = "Auto-sort Downloads folder into categorized subfolders"
    triggers = ["sort downloads", "organize downloads", "auto sort", "clean downloads"]

    def run(self, text: str, lang: str = "en") -> dict:
        download_dir = Path.home() / "Downloads"
        if not download_dir.exists():
            return {"success": False, "speak_en": "Downloads folder not found.", "speak_ta": "Downloads folder இல்ல அண்ணா."}
        sorted_count = 0
        for f in download_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                ext = f.suffix.lower()
                for folder, exts in _RULES.items():
                    if ext in exts:
                        target = download_dir / folder
                        target.mkdir(exist_ok=True)
                        shutil.move(str(f), str(target / f.name))
                        sorted_count += 1
                        break
        if sorted_count:
            return {"success": True, "speak_en": f"Sorted {sorted_count} files.", "speak_ta": f"{sorted_count} files sort பண்ணேன் அண்ணா."}
        return {"success": True, "speak_en": "Nothing to sort.", "speak_ta": "Sort பண்ண files இல்ல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("sort downloads")["speak_en"])
