from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class ParseErrorSkill(BaseCodingSkill):
    name = "parse_error"
    description = "Take a stack trace or error message and explain the root cause in plain language"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "error": {"type": "string", "description": "The error message or stack trace"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["error"]

    async def execute(self, **kwargs) -> SkillResult:
        error_text = kwargs.get("error", "")
        if not error_text:
            return SkillResult(success=False, output="No error text provided")

        explanation_parts = []

        # Extract file/line info from traceback
        import re
        tb_lines = error_text.splitlines()
        file_matches = []
        for line in tb_lines:
            m = re.search(r'File "([^"]+)", line (\d+)', line)
            if m:
                file_matches.append((m.group(1), int(m.group(2))))
            m = re.search(r'(\w+Error):\s*(.+)', line)
            if m:
                explanation_parts.append(f"Error type: {m.group(1)}")
                explanation_parts.append(f"Message: {m.group(2)}")

        if file_matches:
            last_file, last_line = file_matches[-1]
            explanation_parts.append(f"Likely location: {last_file}, line {last_line}")
            fp = Path(last_file)
            if fp.exists():
                try:
                    lines = fp.read_text(encoding="utf-8").splitlines()
                    start = max(0, last_line - 5)
                    end = min(len(lines), last_line + 3)
                    explanation_parts.append("Context:")
                    for i in range(start, end):
                        marker = ">>>" if i + 1 == last_line else "   "
                        explanation_parts.append(f"  {marker} {i+1}: {lines[i]}")
                except Exception:
                    pass

        prompt = (
            f"Explain the root cause of this error in plain language. "
            f"Tell me what went wrong and how to fix it.\n\n{error_text}"
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            llm_explanation = resp["message"]["content"]
        except Exception as e:
            llm_explanation = f"(LLM unavailable: {e})"

        explanation_parts.append("")
        explanation_parts.append(llm_explanation)
        return SkillResult(success=True, output="\n".join(explanation_parts), data={"error": error_text})
