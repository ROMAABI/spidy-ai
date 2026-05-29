import json
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/todos.json")

class MarkTodoSkill(BaseSkill):
    name = "mark_todo"
    description = "Mark a todo item as completed"
    triggers = ["mark done", "complete task", "finish todo", "task done", "done", "completed"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _DATA.exists():
            return {"success": False, "speak_en": "No todos to mark.", "speak_ta": "Todos இல்ல அண்ணா."}
        todos = json.loads(_DATA.read_text())
        for word in text.split():
            if word.isdigit():
                idx = int(word) - 1
                pending = [t for t in todos if not t.get("done")]
                if 0 <= idx < len(pending):
                    for t in todos:
                        if t["content"] == pending[idx]["content"]:
                            t["done"] = True
                            break
                    _DATA.write_text(json.dumps(todos, indent=2))
                    return {"success": True, "speak_en": f"Completed: {pending[idx]['content']}", "speak_ta": "Task complete பண்ணேன் அண்ணா."}
        return {"success": False, "speak_en": "Specify todo number.", "speak_ta": "Todo number சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "index": {"type": "number", "description": "Todo index to mark complete (1-based)"},
        }, "required": ["index"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"done {kwargs.get('index', 1)}")["speak_en"])
