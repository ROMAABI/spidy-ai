import asyncio
from skills.coding.base import SkillResult, BaseCodingSkill


class GenerateFunctionSkill(BaseCodingSkill):
    name = "generate_function"
    description = "Generate a Python function from a natural language description"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "description": {"type": "string", "description": "Natural language description of the function"},
            "language": {"type": "string", "description": "Target programming language (python, javascript, etc)"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["description", "language"]

    async def execute(self, **kwargs) -> SkillResult:
        desc = kwargs.get("description", "")
        lang = kwargs.get("language", "python")
        if not desc:
            return SkillResult(success=False, output="No description provided")

        prompt = (
            f"Generate a {lang} function based on this description:\n\n{desc}\n\n"
            f"Return ONLY the code. Include a docstring. Use proper type hints if in Python."
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

        return SkillResult(success=True, output=code, data={"language": lang, "description": desc})
