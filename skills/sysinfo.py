import psutil
from skills.base_skill import BaseSkill

class SysinfoSkill(BaseSkill):
    name        = "sysinfo"
    description = "System info — RAM, CPU, battery, disk"
    triggers    = [
        "ram", "memory", "cpu", "battery", "disk", "storage",
        "temperature", "temp",
        "system info", "system usage", "system status",
        "how much ram", "how much cpu",
        "நினைவகம்", "பேட்டரி", "சிபியு",
    ]

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        if any(w in text_lower for w in ["ram", "memory", "நினைவகம்"]):
            return self._ram_info(lang)
        elif any(w in text_lower for w in ["cpu", "சிபியு", "processor"]):
            return self._cpu_info(lang)
        elif any(w in text_lower for w in ["battery", "பேட்டரி", "charge"]):
            return self._battery_info(lang)
        elif any(w in text_lower for w in ["disk", "storage", "space"]):
            return self._disk_info(lang)
        else:
            return self._full_info(lang)

    def _ram_info(self, lang: str) -> dict:
        ram = psutil.virtual_memory()
        used  = round(ram.used  / 1e9, 1)
        total = round(ram.total / 1e9, 1)
        pct   = ram.percent
        return {
            "success" : True,
            "speak_en": f"RAM usage is {pct}%. You're using {used} GB out of {total} GB.",
            "speak_ta": f"RAM {pct} சதவீதம் பயன்படுகிறது அண்ணா. {used} GB இல் {total} GB உள்ளது."
        }

    def _cpu_info(self, lang: str) -> dict:
        pct   = psutil.cpu_percent(interval=1)
        cores = psutil.cpu_count()
        return {
            "success" : True,
            "speak_en": f"CPU usage is {pct}% across {cores} cores.",
            "speak_ta": f"CPU {pct} சதவீதம் பயன்படுகிறது அண்ணா. {cores} கோர்கள் உள்ளன."
        }

    def _battery_info(self, lang: str) -> dict:
        battery = psutil.sensors_battery()
        if battery is None:
            return {
                "success" : False,
                "speak_en": "No battery found — you might be on a desktop.",
                "speak_ta": "பேட்டரி இல்ல அண்ணா, desktop போல."
            }
        pct      = round(battery.percent, 1)
        charging = battery.power_plugged
        status   = "charging" if charging else "not charging"
        return {
            "success" : True,
            "speak_en": f"Battery is at {pct}% and {status}.",
            "speak_ta": f"பேட்டரி {pct} சதவீதம் உள்ளது அண்ணா, {'சார்ஜ் ஆகுது' if charging else 'சார்ஜ் இல்ல'}."
        }

    def _disk_info(self, lang: str) -> dict:
        disk  = psutil.disk_usage("/")
        free  = round(disk.free  / 1e9, 1)
        total = round(disk.total / 1e9, 1)
        pct   = disk.percent
        return {
            "success" : True,
            "speak_en": f"Disk usage is {pct}%. {free} GB free out of {total} GB.",
            "speak_ta": f"Disk {pct} சதவீதம் நிரம்பியுள்ளது அண்ணா. {free} GB காலியாக உள்ளது."
        }

    def _full_info(self, lang: str) -> dict:
        ram     = psutil.virtual_memory()
        cpu     = psutil.cpu_percent(interval=0.5)
        battery = psutil.sensors_battery()
        bat_str = f"{round(battery.percent)}%" if battery else "N/A"
        return {
            "success" : True,
            "speak_en": f"CPU {cpu}%, RAM {ram.percent}%, Battery {bat_str}.",
            "speak_ta": f"CPU {cpu} சதவீதம், RAM {ram.percent} சதவீதம், பேட்டரி {bat_str} அண்ணா."
        }