from skills.base_skill import BaseSkill, SkillResult


class BaseCodingSkill(BaseSkill):
    """Coding skills extend the hybrid BaseSkill (triggers + tool schema).

    Subclasses must set:
      name        — short snake_case identifier
      description — plain‑English description
      triggers    — list of keyword phrases for voice activation

    Override:
      run(text, lang)     — trigger‑based voice execution
      async execute(**kw) — LLM tool‑call execution
      _tool_params() + _tool_required() — schema params
    """

    @classmethod
    def _tool_required(cls) -> list[str]:
        """Override to list which parameter names are required."""
        return []
