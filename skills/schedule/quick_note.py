from pathlib import Path
from datetime import datetime
from skills.base_skill import BaseSkill, SkillResult

_NOTES_DIR = Path.home() / "notes"

class QuickNoteSkill(BaseSkill):
    name = "quick_note"
    description = "Save a quick note to ~/notes/ with timestamp"
    triggers = ["quick note", "note down", "note", "write note", "kuru kadai", "take note"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["quick note", "note down", "write note", "note pannu", "kuru kadai", "take note"]:
            t = t.replace(w, "").strip()
        t = t.replace("note", "", 1).strip()
        if not t:
            return {"success": False, "speak_en": "What should I note down?", "speak_ta": "Enna note பண்ணட்டும் அண்ணா?"}
        _NOTES_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = _NOTES_DIR / f"note_{timestamp}.txt"
        filepath.write_text(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{t}\n")
        return {"success": True, "speak_en": f"Note saved: {filepath.name}", "speak_ta": f"Note save பண்ணேன்: {filepath.name}"}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "content": {"type": "string", "description": "Note content to save"},
        }, "required": ["content"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"note down {kwargs['content']}")["speak_en"])
