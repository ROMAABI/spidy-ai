import json
from pathlib import Path
from datetime import datetime
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/todos.json")

def _load():
    if _DATA.exists():
        return json.loads(_DATA.read_text())
    return []

def _save(data):
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(data, indent=2))

class AddTodoSkill(BaseSkill):
    name = "add_todo"
    description = "Add a task to the todo list"
    triggers = ["add todo", "add task", "todo", "to-do", "task", "add pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["add todo", "add task", "new todo", "new task", "todo pannu", "add pannu"]:
            t = t.replace(w, "").strip()
        t = t.replace("add", "").replace("todo", "").replace("task", "").strip()
        if not t:
            return {"success": False, "speak_en": "What task to add?", "speak_ta": "Enna task add பண்ணட்டும் அண்ணா?"}
        todos = _load()
        todos.append({"content": t, "created": datetime.now().isoformat(), "done": False})
        _save(todos)
        return {"success": True, "speak_en": f"Added todo: {t}", "speak_ta": f"Todo add பண்ணேன்: {t}"}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "content": {"type": "string", "description": "Todo task description"},
        }, "required": ["content"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"add todo {kwargs['content']}")["speak_en"])
