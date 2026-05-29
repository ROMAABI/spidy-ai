import re
import subprocess
from core.permissions import classify_command, log_permission, PermissionRequest


ACTION_KEYWORDS = {
    # ── Apps ──────────────────────────────────────────────────────────────────
    r"\bfirefox\b.*(close|kill|muodu|po)": "pkill -f firefox",
    r"\b(close|kill|muodu|po)\b.*\bfirefox\b": "pkill -f firefox",
    r"\bterminal\b.*(open|thira|start)": "kitty &",
    r"\b(open|thira|start)\b.*\bterminal\b": "kitty &",

    # ── Volume ────────────────────────────────────────────────────────────────
    r"\bvolume\b.*\bup\b": "pactl set-sink-volume @DEFAULT_SINK@ +10%",
    r"\bvolume\b.*\bdown\b": "pactl set-sink-volume @DEFAULT_SINK@ -10%",
    r"\bvolume\b.*\b(kammi|kammikko|kuraikku|kuraivo|less|low)\b": "pactl set-sink-volume @DEFAULT_SINK@ -10%",
    r"\b(sound|volume|satham)\b.*\b(jastiyakku|jasti|more|high|increase)\b": "pactl set-sink-volume @DEFAULT_SINK@ +10%",
    r"\bmute\b": "pactl set-sink-mute @DEFAULT_SINK@ toggle",
    r"\b(unmute|sound on|satham on)\b": "pactl set-sink-mute @DEFAULT_SINK@ 0",

    # ── Screenshot ────────────────────────────────────────────────────────────
    r"\bscreenshot\b.*\b(edu|edukko|take|eduppu)\b": "grimblast copy area",
    r"\b(edu|edukko|take)\b.*\bscreenshot\b": "grimblast copy area",
    r"\bscreen\b.*\brecord\b.*\b(start|edu|edukko)\b": "wf-recorder -f /tmp/screen_record.mp4 &",
    r"\bscreen\b.*\brecord\b.*\b(stop|niruthu|nill)\b": "pkill -f wf-recorder",

    # ── Lock / Power ──────────────────────────────────────────────────────────
    r"\block\b.*\b(pann|pan|do)\b": "hyprlock",
    r"\block pann": "hyprlock",
    r"\blogout\b": "hyprctl dispatch exit",
    r"\b(suspend|sleep|thoongu|thoongikko)\b": "systemctl suspend",
    r"\b(hibernate|deep sleep)\b": "systemctl hibernate",
    r"\bsystem\b.*\boff\b.*\b(pann|pan|do)\b": "systemctl poweroff",
    r"\b(poweroff|shutdown|off pann|power off)\b": "systemctl poweroff",
    r"\breboot\b.*\b(pann|pan|do)\b": "systemctl reboot",
    r"\brestart\b.*\b(system|computer|laptop)\b": "systemctl reboot",

    # ── Brightness ────────────────────────────────────────────────────────────
    r"\bbrightness\b.*\b(high|jasti|more|increase|jastiyakku)\b": "brightnessctl set +10%",
    r"\bbrightness\b.*\b(low|kammi|kuraikku|kammikko|less|decrease|kuraivo)\b": "brightnessctl set 10%-",

    # ── Files ──────────────────────────────────────────────────────────────────
    r"\b(files|thunar|nautilus)\b.*\b(open|thira|start)\b": "thunar &",
    r"\b(open|thira|start)\b.*\b(files|thunar|nautilus)\b": "thunar &",

    # ── System info ───────────────────────────────────────────────────────────
    r"\b(battery|charge|battery status)\b": "cat /sys/class/power_supply/BAT0/capacity 2>/dev/null && echo '%'",
    r"\b(ram|memory)\b": "free -h | grep Mem",
    r"\b(cpu|processor)\b": "cat /proc/cpuinfo | grep 'model name' | head -1",
    r"\b(disk|storage|space)\b": "df -h /",
}


def match_action(text: str) -> str | None:
    text_lower = text.lower().strip()
    for pattern, command in ACTION_KEYWORDS.items():
        if re.search(pattern, text_lower):
            return command
    return None


def execute_action(command: str, permission_granted: bool = False) -> dict:
    perm_req = classify_command(command)
    if perm_req and not permission_granted:
        log_permission(command, False, "permission_denied_not_confirmed")
        return {
            "success": False,
            "output": "Permission required",
            "command": command,
            "permission_required": True,
            "permission_request": perm_req,
        }

    try:
        stripped = command.strip()
        if stripped.endswith("&"):
            subprocess.Popen(
                stripped,
                shell=True,
                executable="/usr/bin/fish",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log_permission(command, True, "background_process")
            return {"success": True, "output": "", "command": command}

        result = subprocess.run(
            command,
            shell=True,
            executable="/usr/bin/fish",
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            output = result.stdout.strip()[:200]
            log_permission(command, True, "success")
            return {"success": True, "output": output, "command": command}
        else:
            log_permission(command, False, f"exit_code_{result.returncode}")
            return {
                "success": False,
                "output": result.stderr.strip()[:200],
                "command": command,
            }
    except subprocess.TimeoutExpired:
        log_permission(command, False, "timeout")
        return {"success": False, "output": "Command timed out", "command": command}
    except Exception as e:
        log_permission(command, False, str(e))
        return {"success": False, "output": str(e), "command": command}
