"""
skills/alarm.py  –  Set countdown timers and time-based alarms.
"""
import re
import time
import threading
from datetime import datetime, timedelta
from skills.base_skill import BaseSkill


class AlarmSkill(BaseSkill):
    name        = "alarm"
    description = "Set countdown timers and time-based alarms"
    triggers    = [
        "timer", "alarm", "remind", "reminder", "set timer", "set alarm",
        "after", "minutes", "seconds", "hours", "நிமிடம்", "மணி",
        "remind me", "alert", "wake me",
    ]

    def __init__(self):
        self._speaker = None   # injected by assistant: self.alarm_skill.set_speaker(self.tts.speak)
        self._alarms: list[threading.Thread] = []

    def set_speaker(self, speaker_fn):
        """Inject the TTS speak function so alarms can speak."""
        self._speaker = speaker_fn

    def run(self, text: str, lang: str = "en") -> dict:
        text_lower = text.lower()

        # Try to parse a countdown: "set timer 5 minutes", "after 30 seconds"
        seconds = self._parse_duration(text_lower)
        if seconds:
            return self._set_timer(seconds, lang)

        # Try to parse a clock time: "alarm at 7:30", "remind me at 8 PM"
        alarm_time = self._parse_clock_time(text_lower)
        if alarm_time:
            return self._set_clock_alarm(alarm_time, lang)

        return {
            "success" : False,
            "speak_en": "Please say something like 'set timer 5 minutes' or 'alarm at 7:30'.",
            "speak_ta": "Example: 'set timer 5 minutes' அல்லது 'alarm at 7:30' சொல்லுங்க அண்ணா.",
        }

    # ── timer ─────────────────────────────────────────────────────────────────
    def _set_timer(self, seconds: int, lang: str) -> dict:
        label = self._duration_label(seconds)
        t = threading.Thread(
            target=self._countdown, args=(seconds, lang), daemon=True
        )
        t.start()
        self._alarms.append(t)
        return {
            "success" : True,
            "speak_en": f"Timer set for {label}.",
            "speak_ta": f"{label} timer வைச்சாயிட்டேன் அண்ணா.",
        }

    def _countdown(self, seconds: int, lang: str):
        time.sleep(seconds)
        msg_en = "Time's up! Your timer is done."
        msg_ta = "நேரம் ஆச்சு அண்ணா! Timer முடிஞ்சது."
        self._ring(msg_en if lang == "en" else msg_ta, lang)

    # ── clock alarm ───────────────────────────────────────────────────────────
    def _set_clock_alarm(self, alarm_time: datetime, lang: str) -> dict:
        now = datetime.now()
        delta = alarm_time - now
        if delta.total_seconds() < 0:
            # Assume next day
            alarm_time += timedelta(days=1)
            delta = alarm_time - now

        seconds = int(delta.total_seconds())
        label = alarm_time.strftime("%I:%M %p")
        t = threading.Thread(
            target=self._countdown, args=(seconds, lang), daemon=True
        )
        t.start()
        self._alarms.append(t)
        return {
            "success" : True,
            "speak_en": f"Alarm set for {label}.",
            "speak_ta": f"{label} க்கு alarm வைச்சாயிட்டேன் அண்ணா.",
        }

    # ── ring ──────────────────────────────────────────────────────────────────
    def _ring(self, message: str, lang: str):
        # Play a beep
        try:
            import subprocess
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                stdout=-1, stderr=-1,
            )
        except Exception:
            pass
        if self._speaker:
            self._speaker(message, lang)

    # ── parsing ───────────────────────────────────────────────────────────────
    def _parse_duration(self, text: str) -> int:
        total = 0
        for num, unit in re.findall(
            r"(\d+)\s*(hour|hr|minute|min|second|sec|நிமிடம்|விநாடி)s?",
            text,
        ):
            n = int(num)
            if unit in ("hour", "hr"):
                total += n * 3600
            elif unit in ("minute", "min", "நிமிடம்"):
                total += n * 60
            else:
                total += n
        return total

    def _parse_clock_time(self, text: str) -> datetime | None:
        m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        ampm = m.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        now = datetime.now()
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _duration_label(self, seconds: int) -> str:
        if seconds >= 3600:
            return f"{seconds // 3600} hour(s)"
        if seconds >= 60:
            return f"{seconds // 60} minute(s)"
        return f"{seconds} second(s)"
