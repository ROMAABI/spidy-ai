"""
spidy/context.py — System-aware context builder.

Builds a rich context string that gets injected into the LLM system prompt
so the AI understands the specific machine it's running on.
"""

from spidy.profile import get_profile, profile_summary
from spidy.config import get_config


def build_context(include_profile: bool = True, include_config: bool = True) -> str:
    """Build the full system context block for the LLM system prompt."""
    sections = []

    if include_profile:
        profile = get_profile()
        sections.append("=== SYSTEM PROFILE ===")
        sections.append(profile_summary(profile))

    # Architecture awareness
    sections.append(
        "=== ARCHITECTURE GUIDELINES ==="
        "\n- Arch Linux, EndeavourOS, Hyprland/Wayland"
        "\n- Terminal-first responses (avoid GUI assumptions)"
        "\n- Prioritize lightweight, efficient solutions"
        "\n- Know about Ollama, local LLMs, quantization"
        "\n- Prefer safe fixes — explain risks before actions"
        "\n- Avoid Ubuntu/Debian assumptions"
        "\n- Explain root cause, not just symptoms"
    )

    cfg = get_config() if include_config else None
    if cfg and cfg.debug:
        sections.append(f"[DEBUG] Model: {cfg.brain.local_model} / {cfg.brain.cloud_model}")

    return "\n\n".join(sections)


def build_diagnostic_context(issue: str = "") -> str:
    """Build context specifically for troubleshooting."""
    profile = get_profile()
    ctx = [
        "=== TROUBLESHOOTING CONTEXT ===",
        f"Issue: {issue}" if issue else "",
        profile_summary(profile),
        "",
        "=== RECENT LOGS (last 20 lines of journalctl -n 20) ===",
    ]
    import subprocess
    try:
        r = subprocess.run(["journalctl", "-n", "20", "--no-pager"],
                           capture_output=True, text=True, timeout=10)
        ctx.append(r.stdout.strip() if r.stdout.strip() else "(no recent logs)")
    except Exception:
        ctx.append("(could not read journal)")

    return "\n".join(ctx)
