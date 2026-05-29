"""
spidy/commands/diagnose.py
"""

from spidy.profile import get_profile
from spidy.diagnostics.system import SystemDiagnostics
from spidy.diagnostics.logs import LogDiagnostics
from spidy.diagnostics.hardware import HardwareDiagnostics
from spidy.diagnostics.performance import PerformanceDiagnostics
from spidy.diagnostics.ai import AIDiagnostics


class DiagnoseCommand:
    """spidy diagnose — Full system health check."""

    @staticmethod
    def run(area: str = "all") -> str:
        lines = ["═" * 50, "  SPIDY DIAGNOSTICS", "═" * 50]

        if area in ("all", "system"):
            lines.append("\n── System ──")
            lines.append(SystemDiagnostics.summary())

        if area in ("all", "hardware"):
            lines.append("\n── Hardware ──")
            lines.append(HardwareDiagnostics.summary())

        if area in ("all", "performance", "perf"):
            lines.append("\n── Performance ──")
            lines.append(PerformanceDiagnostics.summary())

        if area in ("all", "logs"):
            lines.append("\n── Log Analysis ──")
            lines.append(LogDiagnostics.summary())

        if area in ("all", "ai"):
            lines.append("\n── AI Infrastructure ──")
            lines.append(AIDiagnostics.summary())

        return "\n".join(lines)

    @staticmethod
    def available_checks() -> str:
        return "Areas: all, system, hardware, performance/perf, logs, ai"
