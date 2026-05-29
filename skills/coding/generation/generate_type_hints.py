import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class GenerateTypeHintsSkill(BaseCodingSkill):
    name = "generate_type_hints"
    description = "Add type annotations to an existing Python file"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the Python file"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["path"]

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        if not path:
            return SkillResult(success=False, output="No path provided")
        fp = Path(path)
        if not fp.exists():
            return SkillResult(success=False, output=f"File not found: {path}")
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Read error: {e}")

        prompt = (
            f"Add Python type hints to the following code. "
            f"Add return type annotations and parameter type annotations where missing. "
            f"Import from typing if needed. Return the COMPLETE updated file.\n\n```python\n{content}\n```"
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat, model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            updated = resp["message"]["content"]
        except Exception as e:
            return SkillResult(success=False, output=f"LLM error: {e}")

        # Write back (strip markdown fence if present)
        if updated.startswith("```"):
            updated = updated.split("\n", 1)[1]
            updated = updated.rsplit("```", 1)[0].strip()

        try:
            fp.write_text(updated, encoding="utf-8")
            output = f"Type hints added to {path}"
        except Exception as e:
            output = f"Generated (write failed: {e}):\n\n{updated}"

        return SkillResult(success=True, output=output)
