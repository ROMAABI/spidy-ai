"""
skills/base_skill.py  –  Hybrid skill base: trigger + tool-schema.

Every skill can be invoked either:
  - by keyword matching (voice/TUI → run())
  - by LLM tool call (Ollama → tool_schema() / execute())
"""


class SkillResult:
    """Standard return for execute()."""

    def __init__(self, success: bool, output: str = "", data: dict | None = None):
        self.success = success
        self.output = output
        self.data = data or {}

    def to_run_dict(self, speak_en: str = "", speak_ta: str = "") -> dict:
        return {
            "success": self.success,
            "speak_en": speak_en or self.output,
            "speak_ta": speak_ta or self.output,
        }


class BaseSkill:
    name: str = ""
    description: str = ""
    triggers: list[str] = []

    # ── trigger-based (voice / TUI) ──────────────────────────────────────────

    def can_handle(self, text: str) -> bool:
        return any(t in text.lower() for t in self.triggers)

    def run(self, text: str, lang: str = "en") -> dict:
        raise NotImplementedError

    # ── tool-call (LLM) ──────────────────────────────────────────────────────

    @classmethod
    def tool_schema(cls) -> dict:
        """Ollama-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": cls._tool_params(),
            },
        }

    @classmethod
    def _tool_params(cls) -> dict:
        """Override to define tool parameters schema."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> SkillResult:
        """Override for LLM-driven execution.  Default: fall back to run()."""
        return SkillResult(success=False, output=f"{self.name} has no tool-call handler yet.")

    # ── helpers shared by skills ─────────────────────────────────────────────

    @staticmethod
    def run_cmd(cmd: list[str], timeout: int = 10) -> str:
        import subprocess
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip() or r.stderr.strip()
        except FileNotFoundError:
            return f"Command not found: {cmd[0]}"
        except Exception as e:
            return str(e)

    @staticmethod
    def run_bg(cmd: list[str]) -> None:
        import subprocess
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
