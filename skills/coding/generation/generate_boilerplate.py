import asyncio
from skills.coding.base import SkillResult, BaseCodingSkill


class GenerateBoilerplateSkill(BaseCodingSkill):
    name = "generate_boilerplate"
    description = "Generate boilerplate for a given type: class / API route / test file / CLI tool"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "type": {"type": "string", "enum": ["class", "api_route", "test_file", "cli_tool"], "description": "Type of boilerplate"},
            "name": {"type": "string", "description": "Name for the component"},
            "language": {"type": "string", "description": "Programming language"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["type", "name", "language"]

    async def execute(self, **kwargs) -> SkillResult:
        btype = kwargs.get("type", "")
        name = kwargs.get("name", "")
        lang = kwargs.get("language", "python")
        if not btype or not name:
            return SkillResult(success=False, output="type and name are required")

        prompt = (
            f"Generate {btype} boilerplate in {lang} named '{name}'. "
            f"Include proper imports, docstrings/comments, and a minimal working example. "
            f"Return ONLY the code."
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat, model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            code = resp["message"]["content"]
        except Exception as e:
            return SkillResult(success=False, output=f"LLM error: {e}")

        return SkillResult(success=True, output=code, data={"type": btype, "name": name, "language": lang})
