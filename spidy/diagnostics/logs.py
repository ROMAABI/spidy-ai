"""
spidy/diagnostics/logs.py — Log analysis for troubleshooting.
"""

import subprocess
import re
from dataclasses import dataclass, field


@dataclass
class LogAnalysis:
    journal_errors: list = field(default_factory=list)
    high_priority_logs: list = field(default_factory=list)
    critical_messages: list = field(default_factory=list)
    recent_auth_failures: int = 0
    oom_events: int = 0
    hyprland_crashes: int = 0
    kernel_warnings: list = field(default_factory=list)
    pkg_errors: list = field(default_factory=list)


def _journal(priority: str = "err", lines: int = 30) -> list[str]:
    try:
        r = subprocess.run(
            ["journalctl", f"-p", priority, "-n", str(lines), "--no-pager", "-q"],
            capture_output=True, text=True, timeout=10,
        )
        return [l for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def _grep_journal(pattern: str, lines: int = 50) -> int:
    try:
        r = subprocess.run(
            ["journalctl", "-n", str(lines), "--no-pager", "-q"],
            capture_output=True, text=True, timeout=10,
        )
        return len(re.findall(pattern, r.stdout, re.I))
    except Exception:
        return 0


class LogDiagnostics:
    """Analyze system logs for errors, crashes, and anomalies."""

    @staticmethod
    def analyze(lines: int = 100) -> LogAnalysis:
        result = LogAnalysis()

        # Recent errors
        errors = _journal("err", lines)
        result.journal_errors = errors[:20]

        # High priority (crit/alert/emerg)
        critical = _journal("crit", lines * 2)
        result.critical_messages = critical[:10]

        # Auth failures
        result.recent_auth_failures = _grep_journal("authentication failure|failed password", lines * 2)

        # OOM
        result.oom_events = _grep_journal("oom-killer|Out of memory", lines * 3)

        # Hyprland crashes
        result.hyprland_crashes = _grep_journal("Hyprland.*crash|hyprland.*segfault", lines * 2)

        # Kernel warnings
        kw = _journal("warn", lines)
        result.kernel_warnings = [l for l in kw if "kernel" in l.lower()][:10]

        # Pacman errors
        try:
            r = subprocess.run(
                ["cat", "/var/log/pacman.log"],
                capture_output=True, text=True, timeout=5,
            )
            pe = [l for l in r.stdout.splitlines() if "error" in l.lower()]
            result.pkg_errors = pe[-10:]
        except Exception:
            pass

        return result

    @staticmethod
    def summary(analysis: LogAnalysis | None = None) -> str:
        if analysis is None:
            analysis = LogDiagnostics.analyze()
        lines = [
            f"Recent journal errors: {len(analysis.journal_errors)}",
            f"Critical messages: {len(analysis.critical_messages)}",
            f"Auth failures: {analysis.recent_auth_failures}",
            f"OOM events: {analysis.oom_events}",
            f"Hyprland crashes: {analysis.hyprland_crashes}",
        ]
        if analysis.hyprland_crashes:
            lines.append("WARNING: Hyprland instability detected — check ~/.config/hypr/")
        if analysis.oom_events:
            lines.append("WARNING: Out of memory events — consider zram or swap adjustment")
        return "\n".join(lines)
