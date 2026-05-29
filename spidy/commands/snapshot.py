"""
spidy/commands/snapshot.py
"""

from spidy.snapshot.collector import SnapshotCollector


class SnapshotCommand:
    """spidy snapshot — Collect or list system snapshots."""

    def __init__(self):
        self.collector = SnapshotCollector()

    def take(self, notes: str = "") -> str:
        snap = self.collector.collect(notes=notes)
        return (
            f"Snapshot saved: {snap.id}\n"
            f"  Time: {snap.timestamp}\n"
            f"  RAM: {snap.ram_pct}% | Disk: {snap.disk_pct}% | Swap: {snap.swap_pct}%\n"
            f"  Processes: {len(snap.top_cpu)} | Packages: {snap.package_count}"
        )

    def list(self) -> str:
        snaps = self.collector.list_snapshots()
        if not snaps:
            return "No snapshots yet. Run `spidy snapshot take`."
        lines = ["Recent snapshots:"]
        for s in snaps[:10]:
            lines.append(f"  {s['id']} — {s['timestamp'][:19]}  (RAM: {s['ram_pct']}%)")
        return "\n".join(lines)

    def compare(self, a: str, b: str) -> str:
        diff = self.collector.compare(a, b)
        if "error" in diff:
            return diff["error"]
        lines = [f"Comparing {a} → {b}", f"  RAM:   {diff['ram_change']}  |  Disk:   {diff['disk_change']}"]
        if diff.get("new_failed_services"):
            lines.append(f"  New failed services: {', '.join(diff['new_failed_services'])}")
        return "\n".join(lines)
