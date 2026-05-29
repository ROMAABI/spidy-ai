import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class GenerateTestsSkill(BaseCodingSkill):
    name = "generate_tests"
    description = "Generate unit tests for an existing function or file"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the source file"},
            "function_name": {"type": "string", "description": "Specific function to test (optional)"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["path"]

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        func_name = kwargs.get("function_name", "")
        if not path:
            return SkillResult(success=False, output="No path provided")
        fp = Path(path)
        if not fp.exists():
            return SkillResult(success=False, output=f"File not found: {path}")
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Read error: {e}")

        target = f"function '{func_name}'" if func_name else "all functions"
        prompt = (
            f"Generate pytest unit tests for {target} in the following file. "
            f"Use pytest style (assert statements). Include edge cases. "
            f"Return ONLY the Python test code.\n\n```python\n{content}\n```"
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat, model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            test_code = resp["message"]["content"]
        except Exception as e:
            return SkillResult(success=False, output=f"LLM error: {e}")

        # Write test file next to source
        test_path = fp.parent / f"test_{fp.stem}.py"
        try:
            test_path.write_text(test_code, encoding="utf-8")
            output = f"Tests written to {test_path}\n\n{test_code}"
        except Exception as e:
            output = f"Generated tests (write failed: {e}):\n\n{test_code}"

        return SkillResult(success=True, output=output, data={"test_path": str(test_path)})
