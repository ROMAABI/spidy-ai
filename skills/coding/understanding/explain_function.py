import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class ExplainFunctionSkill(BaseCodingSkill):
    name = "explain_function"
    description = "Extract and explain a specific function or class from a file"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the source file"},
            "name": {"type": "string", "description": "Function or class name to explain"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["path", "name"]

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        name = kwargs.get("name", "")
        if not path or not name:
            return SkillResult(success=False, output="path and name are required")
        fp = Path(path)
        if not fp.exists():
            return SkillResult(success=False, output=f"File not found: {path}")
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Read error: {e}")

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return SkillResult(success=False, output=f"Syntax error: {e}")

        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
                target_node = node
                break

        if target_node is None:
            return SkillResult(success=False, output=f"'{name}' not found in {path}")

        start_line = target_node.lineno
        end_line = getattr(target_node, "end_lineno", start_line)
        lines = content.splitlines()
        extracted = "\n".join(lines[start_line - 1 : end_line])

        prompt = (
            f"Explain the following {type(target_node).__name__.lower()} '{name}' "
            f"from {path} (lines {start_line}-{end_line}). "
            f"Describe its purpose, parameters, return value, and any side effects.\n\n"
            f"```\n{extracted}\n```"
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            explanation = resp["message"]["content"]
        except Exception as e:
            explanation = f"(LLM explanation unavailable: {e})"

        return SkillResult(
            success=True,
            output=explanation,
            data={"path": path, "name": name, "source": extracted, "start_line": start_line, "end_line": end_line},
        )
