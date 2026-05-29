import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

class ProcessSkill(BaseSkill):
    name = "process"
    description = "Kill a process by name, or list running processes"
    triggers = ["kill process", "kill", "force quit", "stop app", "process", "pid"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        for prefix in ["kill", "force quit", "close", "stop"]:
            if t.startswith(prefix):
                name = t.replace(prefix, "").strip()
                if name:
                    r = subprocess.run(["pkill", "-f", name], capture_output=True, text=True)
                    if r.returncode == 0:
                        return {"success": True, "speak_en": f"Killed {name}.", "speak_ta": f"{name} kill பண்ணேன் அண்ணா."}
                    return {"success": False, "speak_en": f"No process found: {name}", "speak_ta": f"{name} process கிடைக்கல அண்ணா."}
        if "list" in t or "running" in t:
            r = subprocess.run(["ps", "aux", "--sort=-%mem"], capture_output=True, text=True, timeout=5)
            lines = r.stdout.splitlines()[:15]
            return {"success": True, "speak_en": "Processes listed.", "speak_ta": "Process list பாருங்க அண்ணா.", "data": {"processes": lines}}
        return {"success": False, "speak_en": "Say kill <process> or list processes.", "speak_ta": "Kill <process> சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "name": {"type": "string", "description": "Process name to kill"},
        }, "required": ["name"]}

    async def execute(self, **kwargs) -> SkillResult:
        name = kwargs.get("name", "")
        if not name:
            return SkillResult(success=False, output="No process name provided.")
        r = subprocess.run(["pkill", "-f", name], capture_output=True, text=True)
        if r.returncode == 0:
            return SkillResult(success=True, output=f"Killed {name}.")
        return SkillResult(success=False, output=f"No process found: {name}")
