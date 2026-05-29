"""
spidy/diagnostics/hardware.py — Hardware health and diagnostics.
"""

import subprocess
import re
from dataclasses import dataclass, field


@dataclass
class HardwareDiag:
    cpu_temp: str = ""
    cpu_throttling: bool = False
    cpu_freq: str = ""
    ram_usage_pct: float = 0.0
    disk_health: str = ""
    disk_usage_pct: float = 0.0
    battery_health: str = ""
    battery_cycles: int = 0
    gpu_temp: str = ""
    fan_speed: str = ""


def _run(cmd: str, timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception:
        return ""


class HardwareDiagnostics:
    """Check hardware health: temps, throttling, disk, battery."""

    @staticmethod
    def diagnose() -> HardwareDiag:
        r = HardwareDiag()

        # CPU temp (via sensors)
        sensors = _run("sensors -u 2>/dev/null | grep -m1 temp1_input | awk '{print $2}'")
        if sensors:
            try:
                r.cpu_temp = f"{float(sensors):.1f}°C"
            except ValueError:
                r.cpu_temp = sensors

        # CPU frequency
        freq = _run("cat /proc/cpuinfo | grep 'cpu MHz' | head -1 | awk '{print $4}'")
        if freq:
            try:
                r.cpu_freq = f"{float(freq):.0f} MHz"
            except ValueError:
                r.cpu_freq = freq

        # Throttling check
        throttled = _run("cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null")
        r.cpu_throttling = throttled == "1"

        # RAM
        mem = _run("free | grep Mem | awk '{print $3/$2 * 100}'")
        try:
            r.ram_usage_pct = round(float(mem), 1) if mem else 0.0
        except ValueError:
            r.ram_usage_pct = 0.0

        # Disk
        disk = _run("df / | tail -1 | awk '{print $5}'")
        r.disk_usage_pct = float(disk.replace("%", "")) if disk else 0.0

        # SMART health (if available)
        smart = _run("sudo smartctl -H /dev/nvme0n1 2>/dev/null | grep 'SMART overall-health' | awk '{print $NF}'")
        r.disk_health = smart or "unavailable"

        # Battery
        cap = _run("cat /sys/class/power_supply/BAT*/capacity 2>/dev/null | head -1")
        cycles = _run("cat /sys/class/power_supply/BAT*/cycle_count 2>/dev/null | head -1")
        if cap:
            r.battery_health = f"{cap}% capacity"
        if cycles:
            try:
                r.battery_cycles = int(cycles)
            except ValueError:
                pass

        return r

    @staticmethod
    def summary(diag: HardwareDiag | None = None) -> str:
        if diag is None:
            diag = HardwareDiagnostics.diagnose()
        lines = [
            f"CPU: {diag.cpu_temp}" if diag.cpu_temp else "CPU temp: N/A",
            f"CPU freq: {diag.cpu_freq}" if diag.cpu_freq else "",
            f"RAM: {diag.ram_usage_pct}%",
            f"Disk: {diag.disk_usage_pct}% — SMART: {diag.disk_health}",
            f"Battery: {diag.battery_health}" if diag.battery_health else "",
        ]
        if diag.cpu_throttling:
            lines.append("WARNING: CPU throttling detected (no-turbo is ON)")
        return "\n".join(l for l in lines if l)
