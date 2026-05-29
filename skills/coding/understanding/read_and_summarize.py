import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class ReadAndSummarizeSkill(BaseCodingSkill):
    name = "read_and_summarize"
    description = "Read a file and return a plain-English summary of what it does"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to summarize",
            }
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
        if not fp.is_file():
            return SkillResult(success=False, output=f"Not a file: {path}")
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Failed to read file: {e}")

        summary_parts = []
        summary_parts.append(f"File: {fp.name}")
        summary_parts.append(f"Size: {len(content)} bytes, {len(content.splitlines())} lines")

        try:
            tree = ast.parse(content)
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            if classes:
                summary_parts.append(f"Classes: {', '.join(classes)}")
            if funcs:
                summary_parts.append(f"Functions: {', '.join(funcs)}")
        except SyntaxError as e:
            summary_parts.append(f"(Could not parse AST: {e})")

        lang = Path(path).suffix.lstrip(".") or "unknown"
        prompt = (
            f"Summarize the following {lang} file ({fp.name}) in plain English. "
            f"Explain its purpose, inputs, outputs, and key logic.\n\n"
            f"```{lang}\n{content[:4000]}\n```"
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            summary = resp["message"]["content"]
        except Exception as e:
            summary = f"(LLM summary unavailable: {e})"

        summary_parts.append("")
        summary_parts.append(summary)
        return SkillResult(success=True, output="\n".join(summary_parts), data={"path": path, "language": lang})
