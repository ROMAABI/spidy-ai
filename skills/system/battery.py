import asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class BatterySkill(BaseSkill):
    name = "battery"
    description = "Check battery status and switch power mode"
    triggers = ["battery", "charge", "power", "battery status", "battery level", "pattery"]

    @staticmethod
    def _read_bat() -> dict:
        base = Path("/sys/class/power_supply/")
        for d in base.glob("BAT*"):
            cap = d / "capacity"
            status = d / "status"
            if cap.exists():
                pct = int(cap.read_text().strip())
                st = status.read_text().strip() if status.exists() else "Unknown"
                return {"percent": pct, "status": st}
        return {"percent": -1, "status": "No battery"}

    def run(self, text: str, lang: str = "en") -> dict:
        bat = self._read_bat()
        if bat["percent"] < 0:
            return {"success": False, "speak_en": "No battery found.", "speak_ta": "Battery இல்ல அண்ணா."}
        charging = "charging" if "Charg" in bat["status"] else "not charging"
        msg_en = f"Battery at {bat['percent']}%, {charging}."
        msg_ta = f"Battery {bat['percent']}% உள்ளது, {'சார்ஜ் ஆகுது' if 'Charg' in bat['status'] else 'சார்ஜ் இல்ல'}."
        return {"success": True, "speak_en": msg_en, "speak_ta": msg_ta, "data": bat}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        bat = self._read_bat()
        return SkillResult(success=True, output=f"Battery: {bat['percent']}% ({bat['status']})", data=bat)
