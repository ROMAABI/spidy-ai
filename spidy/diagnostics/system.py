"""
spidy/diagnostics/system.py — System-level diagnostics.
"""

import subprocess
import os
from dataclasses import dataclass, field, asdict


@dataclass
class SystemDiagResult:
    boot_time: str = ""
    uptime: str = ""
    load_avg: str = ""
    running_services: list = field(default_factory=list)
    failed_services: list = field(default_factory=list)
    zombie_processes: list = field(default_factory=list)
    top_mem_processes: list = field(default_factory=list)
    top_cpu_processes: list = field(default_factory=list)
    open_connections: int = 0
    swap_usage: str = ""


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"(error: {e})"


class SystemDiagnostics:
    """Check system health: services, processes, uptime, resources."""

    @staticmethod
    def diagnose() -> SystemDiagResult:
        r = SystemDiagResult()
        r.boot_time = _run("who -b | awk '{print $3, $4}'")
        r.uptime = _run("uptime -p")
        r.load_avg = _run("cat /proc/loadavg | awk '{print $1, $2, $3}'")
        r.swap_usage = _run("free -h | awk '/Swap:/ {print $3 \"/\" $2}'")

        # Systemd services
        out = _run("systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}'")
        r.running_services = [s for s in out.splitlines() if s.strip()][:30]

        out = _run("systemctl list-units --type=service --state=failed --no-pager --no-legend | awk '{print $1}'")
        r.failed_services = [s for s in out.splitlines() if s.strip()]

        # Zombie processes
        out = _run("ps aux | awk '$8 ~ /Z/ {print $11}' | head -10")
        r.zombie_processes = [s for s in out.splitlines() if s.strip()]

        # Top memory
        out = _run("ps aux --sort=-%mem | head -6 | awk '{print $11, $4\"%\"}'")
        r.top_mem_processes = [s for s in out.splitlines() if s.strip()]

        # Top CPU
        out = _run("ps aux --sort=-%cpu | head -6 | awk '{print $11, $3\"%\"}'")
        r.top_cpu_processes = [s for s in out.splitlines() if s.strip()]

        # Open connections
        out = _run("ss -tln | wc -l")
        try:
            r.open_connections = int(out.strip()) - 1
        except ValueError:
            r.open_connections = 0

        return r

    @staticmethod
    def summary(diag: SystemDiagResult | None = None) -> str:
        if diag is None:
            diag = SystemDiagnostics.diagnose()
        lines = [
            f"Uptime: {diag.uptime}",
            f"Load: {diag.load_avg}",
            f"Swap: {diag.swap_usage}",
            f"Running services: {len(diag.running_services)}",
            f"Open ports: {diag.open_connections}",
        ]
        if diag.failed_services:
            lines.append(f"FAILED services: {' '.join(diag.failed_services)}")
        if diag.zombie_processes:
            lines.append(f"Zombie procs: {len(diag.zombie_processes)}")
        return "\n".join(lines)
