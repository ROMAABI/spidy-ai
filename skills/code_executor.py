"""
skills/code_executor.py  –  Run Python or Bash snippets on request.
"""
import subprocess
import tempfile
import os
from skills.base_skill import BaseSkill


class CodeExecutorSkill(BaseSkill):
    name        = "code_executor"
    description = "Execute Python or Bash code snippets"
    triggers    = [
        "run code", "execute", "run script", "run python", "run bash",
        "run this", "execute this", "run the code", "code chey",
        "script run", "python run", "bash run",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        if "python" in text_lower:
            return self._run_python(text)
        if "bash" in text_lower or "shell" in text_lower or "script" in text_lower:
            return self._run_bash(text)

        # Generic — try to detect a code block in the text
        if "```python" in text:
            code = self._extract_block(text, "python")
            return self._run_python_code(code)
        if "```bash" in text or "```sh" in text:
            code = self._extract_block(text, "bash") or self._extract_block(text, "sh")
            return self._run_bash_code(code)

        return {
            "success" : False,
            "speak_en": "Please paste the code you want me to run.",
            "speak_ta": "எந்த code run பண்ணணும் அண்ணா?",
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    def _extract_block(self, text: str, lang: str) -> str:
        import re
        m = re.search(rf"```{lang}\n(.*?)```", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    def _run_python(self, text: str) -> dict:
        return {
            "success" : True,
            "speak_en": "Sure! Paste the Python code and I'll run it.",
            "speak_ta": "Python code paste பண்ணுங்க அண்ணா, run பண்றேன்.",
        }

    def _run_bash(self, text: str) -> dict:
        return {
            "success" : True,
            "speak_en": "Ready! Paste the bash script and I'll execute it.",
            "speak_ta": "Bash script paste பண்ணுங்க அண்ணா.",
        }

    def _run_python_code(self, code: str) -> dict:
        if not code:
            return {"success": False, "speak_en": "No Python code found.", "speak_ta": "Code இல்ல அண்ணா."}
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
                f.write(code)
                fname = f.name
            result = subprocess.run(
                ["python3", fname], capture_output=True, text=True, timeout=15
            )
            os.unlink(fname)
            out = (result.stdout or result.stderr or "Done.").strip()[:200]
            return {
                "success" : True,
                "speak_en": f"Done. Output: {out}",
                "speak_ta": f"Run ஆச்சு அண்ணா. Output: {out}",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "speak_en": "Script timed out.", "speak_ta": "Time out ஆச்சு அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": f"Error: {e}"}

    def _run_bash_code(self, code: str) -> dict:
        if not code:
            return {"success": False, "speak_en": "No bash code found.", "speak_ta": "Script இல்ல அண்ணா."}
        try:
            result = subprocess.run(
                ["bash", "-c", code], capture_output=True, text=True, timeout=15
            )
            out = (result.stdout or result.stderr or "Done.").strip()[:200]
            return {
                "success" : True,
                "speak_en": f"Done. {out}",
                "speak_ta": f"Run ஆச்சு அண்ணா. {out}",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "speak_en": "Script timed out.", "speak_ta": "Time out ஆச்சு அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": f"Error: {e}"}
