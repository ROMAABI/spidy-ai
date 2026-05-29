import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict


SESSION_DIR = Path.home() / ".spidy" / "sessions"


@dataclass
class Session:
    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)


class SessionManager:
    def __init__(self):
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, sid: str) -> Path:
        return SESSION_DIR / f"{sid}.json"

    def create(self, metadata: dict | None = None) -> Session:
        now = datetime.now(timezone.utc).isoformat()
        session = Session(
            id=uuid.uuid4().hex[:12],
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._save(session)
        return session

    def get(self, sid: str) -> Session | None:
        path = self._path(sid)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return Session(**data)

    def _save(self, session: Session) -> None:
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._path(session.id).write_text(json.dumps(asdict(session), indent=2))

    def add_message(self, sid: str, role: str, content: str) -> bool:
        session = self.get(sid)
        if not session:
            return False
        session.messages.append({"role": role, "content": content, "ts": datetime.now(timezone.utc).isoformat()})
        self._save(session)
        return True

    def list_sessions(self, limit: int = 20) -> list[dict]:
        sessions = []
        for p in sorted(SESSION_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:limit]:
            data = json.loads(p.read_text())
            sessions.append({
                "id": data["id"],
                "created": data["created_at"][:19],
                "updated": data["updated_at"][:19],
                "messages": len(data.get("messages", [])),
            })
        return sessions

    def delete(self, sid: str) -> bool:
        path = self._path(sid)
        if path.exists():
            path.unlink()
            return True
        return False

    def search(self, query: str) -> list[dict]:
        results = []
        for p in SESSION_DIR.glob("*.json"):
            data = json.loads(p.read_text())
            for msg in data.get("messages", []):
                if query.lower() in msg.get("content", "").lower():
                    results.append({"session_id": data["id"], "message": msg["content"][:200], "role": msg["role"]})
                    break
        return results


import os
