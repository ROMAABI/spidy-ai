import re
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

LOG_DIR = Path.home() / ".local" / "share" / "spidy"
LOG_FILE = LOG_DIR / "permissions.jsonl"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


PRIVILEGE_PATTERNS = [
    (r"\bsudo\b", "root privilege", RiskLevel.HIGH),
    (r"\bpkexec\b", "polkit privilege", RiskLevel.HIGH),
    (r"\bdoas\b", "root privilege", RiskLevel.HIGH),
    (r"\bsu\b", "switch user", RiskLevel.HIGH),
]

HIGH_RISK_PATTERNS = [
    (r"\brm\s+.*-rf\b", "recursive forced deletion", RiskLevel.CRITICAL),
    (r"\brm\s+.*-fr\b", "recursive forced deletion", RiskLevel.CRITICAL),
    (r"\bmkfs\b", "filesystem formatting", RiskLevel.CRITICAL),
    (r"\bfdisk\b", "disk partitioning", RiskLevel.CRITICAL),
    (r"\bdd\b", "raw disk write", RiskLevel.CRITICAL),
    (r"\bchmod\s+.*-R\b", "recursive permission change", RiskLevel.HIGH),
    (r"\bchown\s+.*-R\b", "recursive ownership change", RiskLevel.HIGH),
    (r"\bkill\s+-9\b", "forced process kill", RiskLevel.MEDIUM),
    (r"\bkillall\b", "kill all matching", RiskLevel.MEDIUM),
    (r"\bpkill\b", "process kill", RiskLevel.LOW),
    (r"\bsystemctl\s+(stop|disable|mask)\b", "service disruption", RiskLevel.HIGH),
    (r"\binsmod\b", "kernel module load", RiskLevel.CRITICAL),
    (r"\bmodprobe\b", "kernel module load", RiskLevel.HIGH),
    (r"\bshred\b", "secure file deletion", RiskLevel.HIGH),
    (r"\bmv\s+.*/\s*\.\.", "move to parent", RiskLevel.MEDIUM),
    (r"\bsudo\b", "root privilege", RiskLevel.HIGH),
    (r"\bpkexec\b", "polkit privilege", RiskLevel.HIGH),
    (r"\bdoas\b", "root privilege", RiskLevel.HIGH),
    (r"\bsu\b", "switch user", RiskLevel.HIGH),
]


@dataclass
class PermissionRequest:
    command: str
    reason: str
    risk_level: RiskLevel
    requires_safety_phrase: bool = False
    safety_phrase: str = ""


def classify_command(command: str) -> PermissionRequest | None:
    cmd_lower = command.lower()

    for pattern, reason, risk in HIGH_RISK_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            requires_safety = risk == RiskLevel.CRITICAL
            return PermissionRequest(
                command=command,
                reason=reason,
                risk_level=risk,
                requires_safety_phrase=requires_safety,
                safety_phrase="I UNDERSTAND THE RISKS" if requires_safety else "",
            )

    return None


def log_permission(command: str, granted: bool, reason: str = "") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "granted": granted,
        "reason": reason,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_permission_prompt(req: PermissionRequest) -> str:
    risk_label = {
        RiskLevel.LOW: "LOW",
        RiskLevel.MEDIUM: "MEDIUM",
        RiskLevel.HIGH: "HIGH",
        RiskLevel.CRITICAL: "CRITICAL",
    }[req.risk_level]

    lines = [
        f"⚠ Permission Required",
        f"Command: {req.command}",
        f"Reason: {req.reason}",
        f"Risk: {risk_label}",
    ]

    if req.requires_safety_phrase:
        lines.append(f"To confirm, type: {req.safety_phrase}")
    else:
        lines.append("Type 'yes' to confirm, 'no' to deny.")

    return "\n".join(lines)


def get_voice_prompt(req: PermissionRequest) -> str:
    if req.requires_safety_phrase:
        return (
            f"This is a critical command that could cause data loss. "
            f"Reason: {req.reason}. "
            f"Say 'I understand the risks' to confirm, or 'no' to cancel."
        )
    return (
        f"This command requires administrator privileges. "
        f"Reason: {req.reason}. "
        f"Do you want me to continue?"
    )


def validate_confirmation(confirmation: str, req: PermissionRequest) -> bool:
    if req.requires_safety_phrase:
        return confirmation.strip().upper() == req.safety_phrase
    return confirmation.strip().lower() in ("yes", "y", "confirm", "proceed", "do it")
