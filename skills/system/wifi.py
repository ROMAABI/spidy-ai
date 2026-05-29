import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

def _nmcli(*args: str) -> str:
    try:
        r = subprocess.run(["nmcli"] + list(args), capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return str(e)

class WifiSkill(BaseSkill):
    name = "wifi"
    description = "Turn WiFi on/off, list networks, or connect to a network"
    triggers = ["wifi", "wireless", "network", "internet", "wifi on", "wifi off"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "on" in t or "enable" in t:
            _nmcli("radio", "wifi", "on")
            return {"success": True, "speak_en": "WiFi turned on.", "speak_ta": "WiFi on பண்ணேன் அண்ணா."}
        if "off" in t or "disable" in t:
            _nmcli("radio", "wifi", "off")
            return {"success": True, "speak_en": "WiFi turned off.", "speak_ta": "WiFi off பண்ணேன் அண்ணா."}
        if "list" in t or "show" in t or "available" in t:
            out = _nmcli("device", "wifi", "list")
            lines = out.splitlines()[:10]
            return {"success": True, "speak_en": "Networks listed.", "speak_ta": "Networks பாருங்க அண்ணா.", "data": {"networks": lines}}
        return {"success": True, "speak_en": _nmcli("device", "status").splitlines()[-1], "speak_ta": "WiFi status பாருங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["on", "off", "status", "list"], "description": "WiFi action"},
            "ssid": {"type": "string", "description": "Network SSID to connect to"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        action = kwargs.get("action", "")
        if action == "list":
            out = _nmcli("device", "wifi", "list")
            return SkillResult(success=True, output=out[:500])
        return SkillResult(success=True, output=self.run(action)["speak_en"])
