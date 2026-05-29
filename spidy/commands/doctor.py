"""
spidy/commands/doctor.py
"""

import subprocess

from spidy.diagnostics.system import SystemDiagnostics
from spidy.diagnostics.logs import LogDiagnostics
from spidy.diagnostics.hardware import HardwareDiagnostics
from spidy.diagnostics.performance import PerformanceDiagnostics
from spidy.profile import get_profile


class DoctorCommand:
    """spidy doctor — AI-powered health check with recommendations."""

    @staticmethod
    def run() -> str:
        profile = get_profile()
        perf = PerformanceDiagnostics.diagnose()
        hw = HardwareDiagnostics.diagnose()
        logs = LogDiagnostics.analyze()
        sysd = SystemDiagnostics.diagnose()

        issues = []
        recommendations = []

        # CPU throttling
        if hw.cpu_throttling:
            issues.append("CPU throttling active (no-turbo is ON)")
            recommendations.append("Run: echo '1' | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo")

        # RAM pressure
        if perf.ram_pct > 80:
            issues.append(f"High RAM usage: {perf.ram_pct:.0f}%")
            recommendations.append("Close heavy applications or add swap/zram")
            recommendations.append("Consider: sudo pacman -S zram-generator")

        # Swap pressure
        if perf.swap_pct > 30:
            issues.append(f"Significant swap usage: {perf.swap_pct:.0f}%")
            recommendations.append(f"Current swappiness: {perf.swapiness}. Set vm.swappiness=10")

        # Failed services
        if sysd.failed_services:
            issues.append(f"Failed systemd services: {len(sysd.failed_services)}")
            for svc in sysd.failed_services[:3]:
                recommendations.append(f"Check: journalctl -xu {svc}")

        # OOM
        if logs.oom_events > 0:
            issues.append(f"Out-of-memory events detected: {logs.oom_events}")
            recommendations.append("Increase swap or enable zram. Check: dmesg | grep oom")

        # Hyprland crashes
        if logs.hyprland_crashes > 0:
            issues.append(f"Hyprland crashes: {logs.hyprland_crashes}")
            recommendations.append("Check: ~/.config/hypr/hyprland.conf for errors")
            recommendations.append("Check: journalctl -f -o cat /usr/bin/Hyprland")

        # Disk
        if hw.disk_usage_pct > 85:
            issues.append(f"Disk usage critical: {hw.disk_usage_pct}%")
            recommendations.append("Clean pkg cache: sudo pacman -Scc")
            recommendations.append("Run: ncdu / to find large files")

        # Ollama
        if not profile.ai.ollama_running:
            issues.append("Ollama is not running")
            recommendations.append("Start: systemctl --user start ollama")
        else:
            # Estimate total model RAM from Ollama model list
            total_model_ram = _estimate_ollama_ram()
            if total_model_ram > 12:
                issues.append(f"LLM models may exceed RAM: ~{total_model_ram:.1f}GB loaded")
                recommendations.append("Use smaller quantized models (Q4_K_M or Q5_K_M)")

        output = ["═" * 50, "  SPIDY DOCTOR — System Health Report", "═" * 50]

        if issues:
            output.append(f"\nIssues found: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                output.append(f"  {i}. {issue}")
            output.append(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                output.append(f"  {i}. {rec}")
        else:
            output.append("\nNo issues detected. System looks healthy.")

        return "\n".join(output)


def _estimate_ollama_ram() -> float:
    """Approximate total GB occupied by loaded Ollama models.

    Parses ``ollama list`` output, sums up model sizes.
    Falls back to 0.0 on failure.
    """
    try:
        out = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        total = 0.0
        for line in out.strip().splitlines()[1:]:  # skip header
            parts = line.split()
            if len(parts) >= 3:
                try:
                    size_str = parts[2].upper()
                    if "GB" in size_str:
                        total += float(size_str.replace("GB", "").strip())
                    elif "MB" in size_str:
                        total += float(size_str.replace("MB", "").strip()) / 1024
                except (ValueError, IndexError):
                    continue
        return total
    except Exception:
        return 0.0
