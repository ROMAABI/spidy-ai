"""
spidy/snapshot/collector.py — System snapshot collector.

Captures a point-in-time snapshot of system state for later comparison
and troubleshooting.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict


_SNAPSHOT_DIR = Path.home() / ".local/share/spidy/snapshots"


@dataclass
class SystemSnapshot:
    id: str = ""
    timestamp: str = ""
    # Metadata
    kernel: str = ""
    uptime: str = ""
    # Resources
    cpu_load: str = ""
    ram_pct: float = 0.0
    swap_pct: float = 0.0
    disk_pct: float = 0.0
    # Processes
    top_cpu: list = field(default_factory=list)
    top_mem: list = field(default_factory=list)
    # Network
    ip: str = ""
    wifi_ssid: str = ""
    # Services
    failed_services: list = field(default_factory=list)
    # Packages
    package_count: int = 0
    # AI
    ollama_models: list = field(default_factory=list)
    # Custom
    notes: str = ""


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


class SnapshotCollector:
    """Collect and manage system snapshots."""

    def __init__(self, snapshot_dir: str | Path = ""):
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else _SNAPSHOT_DIR
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, notes: str = "") -> SystemSnapshot:
        snap = SystemSnapshot(
            timestamp=datetime.now().isoformat(),
            id=datetime.now().strftime("snap_%Y%m%d_%H%M%S"),
            kernel=_run("uname -r"),
            uptime=_run("uptime -p"),
            cpu_load=_run("cat /proc/loadavg | awk '{print $1, $2, $3}'"),
        )
        # RAM
        try:
            snap.ram_pct = float(_run("free | grep Mem | awk '{print $3/$2 * 100}'") or 0)
        except ValueError:
            pass
        # Swap
        try:
            swap_total = float(_run("free | grep Swap | awk '{print $2}'") or 0)
            swap_used = float(_run("free | grep Swap | awk '{print $3}'") or 0)
            snap.swap_pct = round(swap_used / swap_total * 100, 1) if swap_total > 0 else 0
        except (ValueError, ZeroDivisionError):
            pass
        # Disk
        disk_out = _run("df / | tail -1 | awk '{print $5}'")
        try:
            snap.disk_pct = float(disk_out.replace("%", ""))
        except ValueError:
            pass
        # Top processes
        snap.top_cpu = _run("ps aux --sort=-%cpu | head -6 | awk '{print $11}'").splitlines()
        snap.top_mem = _run("ps aux --sort=-%mem | head -6 | awk '{print $11}'").splitlines()
        # Network
        snap.ip = _run("ip a show | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}'")
        snap.wifi_ssid = _run("nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2")
        # Services
        snap.failed_services = _run("systemctl list-units --type=service --state=failed --no-pager --no-legend | awk '{print $1}'").splitlines()
        # Packages
        pkg_count = _run("pacman -Q | wc -l")
        try:
            snap.package_count = int(pkg_count)
        except ValueError:
            pass
        # Ollama
        snap.ollama_models = _run("ollama list 2>/dev/null | tail -n+2 | awk '{print $1}'").splitlines()
        snap.notes = notes

        self._save(snap)
        return snap

    def _save(self, snap: SystemSnapshot):
        path = self.snapshot_dir / f"{snap.id}.json"
        path.write_text(json.dumps(asdict(snap), indent=2))

    def list_snapshots(self) -> list[dict]:
        snaps = []
        for f in sorted(self.snapshot_dir.glob("snap_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text())
                snaps.append({
                    "id": data.get("id", f.stem),
                    "timestamp": data.get("timestamp", ""),
                    "ram_pct": data.get("ram_pct", 0),
                    "disk_pct": data.get("disk_pct", 0),
                })
            except Exception:
                continue
        return snaps

    def get_snapshot(self, snap_id: str) -> SystemSnapshot | None:
        path = self.snapshot_dir / f"{snap_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return SystemSnapshot(**data)
        except Exception:
            return None

    def compare(self, snap_id_a: str, snap_id_b: str) -> dict:
        a = self.get_snapshot(snap_id_a)
        b = self.get_snapshot(snap_id_b)
        if not a or not b:
            return {"error": "Snapshot not found"}
        return {
            "time_between": f"{a.timestamp} → {b.timestamp}",
            "ram_change": f"{b.ram_pct - a.ram_pct:+.1f}%",
            "disk_change": f"{b.disk_pct - a.disk_pct:+.1f}%",
            "swap_change": f"{b.swap_pct - a.swap_pct:+.1f}%",
            "new_failed_services": [s for s in b.failed_services if s not in a.failed_services],
        }

    def latest(self) -> SystemSnapshot | None:
        snaps = self.list_snapshots()
        if snaps:
            return self.get_snapshot(snaps[0]["id"])
        return None
