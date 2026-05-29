import asyncio
import psutil
from skills.base_skill import BaseSkill, SkillResult

class SystemStatsSkill(BaseSkill):
    name = "system_stats"
    description = "Show system resource usage: CPU, RAM, disk, and temperature"
    triggers = ["system stats", "cpu", "ram", "memory", "disk usage", "system info", "system status"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "cpu" in t:
            pct = psutil.cpu_percent(interval=1)
            return {"success": True, "speak_en": f"CPU usage is {pct}% across {psutil.cpu_count()} cores.", "speak_ta": f"CPU {pct}% பயன்படுகிறது அண்ணா."}
        if any(w in t for w in ["ram", "memory"]):
            ram = psutil.virtual_memory()
            return {"success": True, "speak_en": f"RAM: {ram.percent}% used ({ram.used//1e9:.1f}/{ram.total//1e9:.1f} GB).", "speak_ta": f"RAM {ram.percent}% பயன்படுகிறது அண்ணா."}
        if any(w in t for w in ["disk", "storage"]):
            d = psutil.disk_usage("/")
            return {"success": True, "speak_en": f"Disk: {d.percent}% used ({d.free//1e9:.1f} GB free).", "speak_ta": f"Disk {d.percent}% நிரம்பியுள்ளது அண்ணா."}
        ram = psutil.virtual_memory()
        d = psutil.disk_usage("/")
        msg = f"CPU: {psutil.cpu_percent(interval=1)}% | RAM: {ram.percent}% | Disk: {d.percent}%"
        return {"success": True, "speak_en": msg, "speak_ta": msg, "data": {"cpu": psutil.cpu_percent(interval=1), "ram": ram.percent, "disk": d.percent}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        d = psutil.disk_usage("/")
        ram = psutil.virtual_memory()
        return SkillResult(success=True, output=f"CPU: {psutil.cpu_percent(interval=1)}%, RAM: {ram.percent}%, Disk: {d.percent}%",
                          data={"cpu": psutil.cpu_percent(interval=1), "ram": ram.percent, "disk": d.percent})
