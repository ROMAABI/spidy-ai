import json
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/todos.json")

class ListTodosSkill(BaseSkill):
    name = "list_todos"
    description = "List all pending todo items"
    triggers = ["list todos", "show todos", "my tasks", "pending tasks", "task list"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _DATA.exists():
            return {"success": True, "speak_en": "No todos yet.", "speak_ta": "Todos இல்ல அண்ணா."}
        todos = json.loads(_DATA.read_text())
        pending = [t for t in todos if not t.get("done")]
        if not pending:
            return {"success": True, "speak_en": "All todos completed!", "speak_ta": "Ellame complete aagiduchu அண்ணா!"}
        lines = [f"{i+1}. {t['content']}" for i, t in enumerate(pending)]
        return {"success": True, "speak_en": f"You have {len(pending)} tasks.", "speak_ta": f"{len(pending)} tasks உள்ளது அண்ணா.", "data": {"todos": pending}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        todos = json.loads(_DATA.read_text()) if _DATA.exists() else []
        pending = [t for t in todos if not t.get("done")]
        return SkillResult(success=True, output=f"{len(pending)} tasks pending.", data={"todos": pending})
