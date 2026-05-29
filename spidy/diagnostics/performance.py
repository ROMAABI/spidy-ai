"""
spidy/diagnostics/performance.py — System performance analysis.
"""

import subprocess
from dataclasses import dataclass, field


@dataclass
class PerfDiag:
    cpu_load_pct: float = 0.0
    ram_pct: float = 0.0
    swap_pct: float = 0.0
    disk_io: str = ""
    net_io: str = ""
    zram_active: bool = False
    zram_size: str = ""
    swapiness: int = 60
    oom_score: str = ""
    slow_apps: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


def _run(cmd: str, timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception:
        return ""


class PerformanceDiagnostics:
    """Analyze performance: resource pressure, bottlenecks, recommendations."""

    @staticmethod
    def diagnose() -> PerfDiag:
        r = PerfDiag()

        # CPU load (1 min)
        load = _run("cat /proc/loadavg | awk '{print $1}'")
        try:
            r.cpu_load_pct = float(load) * 100 if load else 0
        except ValueError:
            pass

        # RAM
        r.ram_pct = float(_run("free | grep Mem | awk '{print $3/$2 * 100}'") or 0)

        # Swap
        swap_total = _run("free | grep Swap | awk '{print $2}'")
        swap_used = _run("free | grep Swap | awk '{print $3}'")
        try:
            st, su = float(swap_total), float(swap_used)
            r.swap_pct = round(su / st * 100, 1) if st > 0 else 0
        except (ValueError, ZeroDivisionError):
            r.swap_pct = 0

        # ZRAM
        zram = _run("zramctl 2>/dev/null | tail -1 | awk '{print $2}'")
        if zram:
            r.zram_active = True
            r.zram_size = zram

        # Swappiness
        sw = _run("cat /proc/sys/vm/swappiness")
        try:
            r.swapiness = int(sw)
        except (ValueError, TypeError):
            pass

        # Disk I/O
        r.disk_io = _run("iostat -x 1 2 2>/dev/null | tail -5 | head -1 | awk '{print $2, \"%util\"}'") or "N/A"

        # OOM score of current process
        r.oom_score = _run("cat /proc/self/oom_score")

        # Recommendations
        if r.swap_pct > 50:
            r.recommendations.append("High swap usage — add more RAM or enable zram")
        if r.ram_pct > 85:
            r.recommendations.append("RAM pressure — close heavy apps or add swap/zram")
        if r.swapiness > 60:
            r.recommendations.append("swappiness is high — set vm.swappiness=10 for better responsiveness")
        if not r.zram_active:
            r.recommendations.append("zram not active — enables compressed RAM swap. Install zram-generator")

        return r

    @staticmethod
    def summary(diag: PerfDiag | None = None) -> str:
        if diag is None:
            diag = PerformanceDiagnostics.diagnose()
        lines = [
            f"CPU load: {diag.cpu_load_pct:.0f}%",
            f"RAM: {diag.ram_pct:.0f}%  |  Swap: {diag.swap_pct:.0f}%  |  Swappiness: {diag.swapiness}",
            f"ZRAM: {diag.zram_size if diag.zram_active else 'inactive'}",
            f"Disk I/O: {diag.disk_io}",
        ]
        if diag.recommendations:
            lines.append("Recommendations:")
            lines.extend(f"  - {r}" for r in diag.recommendations)
        return "\n".join(lines)
