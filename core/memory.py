import sqlite3
import yaml
import chromadb
from datetime import datetime

with open("config.yaml") as f:
    config = yaml.safe_load(f)

MEM = config["memory"]

class Memory:
    def __init__(self):
        # SQLite — conversation history
        self.conn = sqlite3.connect(MEM["sqlite_path"], check_same_thread=False)
        self._init_db()

        # ChromaDB — semantic/vector memory
        self.chroma = chromadb.PersistentClient(path=MEM["chroma_path"])
        self.collection = self.chroma.get_or_create_collection("spidy_memory")

        self.max_history = MEM["max_history"]

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add(self, role: str, content: str):
        ts = datetime.now().isoformat()
        # Save to SQLite
        self.conn.execute(
            "INSERT INTO history (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, ts)
        )
        self.conn.commit()

        # Save to ChromaDB for semantic recall
        uid = f"{role}_{ts}"
        self.collection.add(
            documents=[content],
            metadatas=[{"role": role, "timestamp": ts}],
            ids=[uid]
        )

    def get_history(self) -> list:
        rows = self.conn.execute(
            "SELECT role, content FROM history ORDER BY id DESC LIMIT ?",
            (self.max_history,)
        ).fetchall()
        # Return in chronological order
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def search(self, query: str, n=3) -> list:
        """Semantic search — find relevant past context"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n
        )
        return results["documents"][0] if results["documents"] else []

    def clear(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()