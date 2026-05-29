import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

def _btctl(*args: str) -> str:
    try:
        r = subprocess.run(["bluetoothctl"] + list(args), capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return str(e)

class BluetoothSkill(BaseSkill):
    name = "bluetooth"
    description = "Control Bluetooth: on/off, scan, pair, list devices"
    triggers = ["bluetooth", "bt", "bluetooth on", "bluetooth off"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "on" in t or "enable" in t:
            _ = subprocess.run(["systemctl", "--user", "start", "bluetooth.service"], capture_output=True)
            subprocess.run(["bluetoothctl", "power", "on"], capture_output=True)
            return {"success": True, "speak_en": "Bluetooth turned on.", "speak_ta": "Bluetooth on பண்ணேன் அண்ணா."}
        if "off" in t or "disable" in t:
            subprocess.run(["bluetoothctl", "power", "off"], capture_output=True)
            return {"success": True, "speak_en": "Bluetooth turned off.", "speak_ta": "Bluetooth off பண்ணேன் அண்ணா."}
        if "list" in t or "paired" in t or "show" in t:
            out = _btctl("paired-devices")
            return {"success": True, "speak_en": out[:200], "speak_ta": "Bluetooth devices பாருங்க அண்ணா."}
        if "scan" in t or "find" in t:
            out = _btctl("scan", "on")
            return {"success": True, "speak_en": "Scanning for devices.", "speak_ta": "Scan பண்றேன் அண்ணா."}
        return {"success": True, "speak_en": _btctl("show")[:200], "speak_ta": "Bluetooth status பாருங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["on", "off", "list", "scan"], "description": "Bluetooth action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("action", ""))["speak_en"])
