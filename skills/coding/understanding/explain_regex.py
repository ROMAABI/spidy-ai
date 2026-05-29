import asyncio
import re
from skills.coding.base import SkillResult, BaseCodingSkill


class ExplainRegexSkill(BaseCodingSkill):
    name = "explain_regex"
    description = "Explain what a regex pattern matches in plain English with examples"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "pattern": {"type": "string", "description": "The regex pattern to explain"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["pattern"]

    async def execute(self, **kwargs) -> SkillResult:
        pattern = kwargs.get("pattern", "")
        if not pattern:
            return SkillResult(success=False, output="No pattern provided")

        parts = []
        parts.append(f"Pattern: `{pattern}`")
        parts.append("")

        # Compile check
        try:
            compiled = re.compile(pattern)
            parts.append("✅ Valid regex")
        except re.error as e:
            return SkillResult(success=False, output=f"Invalid regex: {e}")

        # Breakdown
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": f"Explain this regex pattern in plain English with examples. Break it down token by token.\n\nPattern: `{pattern}`"}],
                stream=False,
            )
            explanation = resp["message"]["content"]
        except Exception as e:
            explanation = f"(LLM explanation unavailable: {e})"

        parts.append(explanation)
        parts.append("")

        # Test examples
        test_strings = [
            "hello123",
            "abc-123",
            "test@example.com",
            "2024-01-01",
            "/path/to/file",
        ]
        parts.append("Match tests:")
        for ts in test_strings:
            m = compiled.search(ts)
            result = f"  '{ts}' → {'✅ ' + repr(m.group()) if m else '❌ no match'}"
            parts.append(result)

        return SkillResult(success=True, output="\n".join(parts), data={"pattern": pattern})
