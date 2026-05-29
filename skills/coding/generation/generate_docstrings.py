import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class GenerateDocstringsSkill(BaseCodingSkill):
    name = "generate_docstrings"
    description = "Add docstrings to all functions in a file that are missing them"

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

        tree = ast.parse(content)
        missing = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   and not (isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)
                            and isinstance(n.body[0].value.value, str))]
        if not missing:
            return SkillResult(success=True, output="All functions/classes already have docstrings.")

        names = [n.name for n in missing]
        prompt = (
            f"Add Google-style docstrings to the following functions/classes in this Python file. "
            f"Return the COMPLETE updated file with docstrings added. "
            f"Missing docstrings for: {', '.join(names)}\n\n```python\n{content}\n```"
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

        if updated.startswith("```"):
            updated = updated.split("\n", 1)[1]
            updated = updated.rsplit("```", 1)[0].strip()

        try:
            fp.write_text(updated, encoding="utf-8")
            output = f"Docstrings added to: {', '.join(names)}"
        except Exception as e:
            output = f"Generated (write failed: {e})"

        return SkillResult(success=True, output=output, data={"updated": [str(n) for n in names]})
