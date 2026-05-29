import subprocess
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_NOTES_DIR = Path.home() / "notes"

class NoteSearchSkill(BaseSkill):
    name = "note_search"
    description = "Search notes by keyword (grep through ~/notes/)"
    triggers = ["search notes", "find note", "note search", "look up notes", "notes la"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _NOTES_DIR.exists():
            return {"success": False, "speak_en": "No notes directory found.", "speak_ta": "Notes directory இல்ல அண்ணா."}
        t = text
        for w in ["search notes", "find note", "note search", "look up notes", "find", "notes la", "search"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "What keyword to search?", "speak_ta": "Enna keyword search பண்ணட்டும் அண்ணா?"}
        try:
            r = subprocess.run(["grep", "-ril", t, str(_NOTES_DIR)], capture_output=True, text=True, timeout=10)
            if r.stdout.strip():
                files = r.stdout.strip().splitlines()
                names = [Path(f).name for f in files[:10]]
                return {"success": True, "speak_en": f"Found {len(files)} notes.", "speak_ta": f"{len(files)} notes கிடைத்தது அண்ணா.", "data": {"files": names}}
            return {"success": True, "speak_en": "No matching notes.", "speak_ta": "Notes கிடைக்கல அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Search error: {e}", "speak_ta": "Search error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "keyword": {"type": "string", "description": "Keyword to search in notes"},
        }, "required": ["keyword"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"search notes {kwargs['keyword']}")["speak_en"])
