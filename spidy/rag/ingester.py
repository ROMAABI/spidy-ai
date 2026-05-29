"""
spidy/rag/ingester.py — File ingestion pipeline for the knowledge base.

Ingests markdown notes, configs, logs, shell scripts, and other files
into the vector database for semantic retrieval.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field


SUPPORTED_EXTS = {".md", ".txt", ".log", ".conf", ".json", ".yaml", ".yml",
                  ".service", ".sh", ".py", ".toml", ".ini", ".cfg"}


@dataclass
class IngestedDoc:
    path: str = ""
    content: str = ""
    summary: str = ""
    doc_type: str = ""
    tags: list = field(default_factory=list)
    hash: str = ""
    ingested_at: str = ""


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _detect_type(path: str) -> str:
    name = Path(path).name.lower()
    if name.endswith(".md"): return "markdown"
    if name.endswith(".log"): return "log"
    if name.endswith(".conf") or name.endswith(".cfg") or name.endswith(".ini"): return "config"
    if name.endswith(".json"): return "json"
    if name.endswith(".yaml") or name.endswith(".yml"): return "yaml"
    if name.endswith(".service"): return "systemd"
    if name.endswith(".sh"): return "shell"
    if name.endswith(".py"): return "python"
    if name.endswith(".toml"): return "toml"
    if name.endswith(".txt"): return "text"
    return "unknown"


def _infer_tags(path: str, content: str) -> list[str]:
    tags = set()
    p = Path(path)
    # Directory-based tags
    for part in p.parts:
        if part in ("config", "conf", "logs", "notes", "scripts", "dotfiles"):
            tags.add(part)

    # Content-based tags
    if "error" in content.lower() or "fail" in content.lower():
        tags.add("error")
    if "install" in content.lower() or "pacman" in content.lower() or "yay" in content.lower():
        tags.add("package")
    if "hyprland" in content.lower() or "hyprctl" in content.lower():
        tags.add("hyprland")
    if "nvidia" in content.lower():
        tags.add("nvidia")
    if "ollama" in content.lower() or "llama" in content.lower() or "model" in content.lower():
        tags.add("ai")
    if "permission" in content.lower() or "access" in content.lower():
        tags.add("security")
    return sorted(tags)


class KnowledgeIngester:
    """Ingest files into the knowledge base."""

    def __init__(self, kb_dir: str | Path = ""):
        self.kb_dir = Path(kb_dir or Path.home() / ".local/share/spidy/knowledge")
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.kb_dir / "index.json"
        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            self.index = json.loads(self.index_path.read_text())
        else:
            self.index = {}

    def _save_index(self):
        self.index_path.write_text(json.dumps(self.index, indent=2))

    def ingest_file(self, path: str | Path) -> IngestedDoc | None:
        path = Path(path)
        if not path.exists() or not path.is_file():
            return None
        if path.suffix.lower() not in SUPPORTED_EXTS:
            return None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        h = _hash_content(content)
        if self.index.get(str(path)) == h:
            return None  # unchanged

        doc_type = _detect_type(str(path))
        tags = _infer_tags(str(path), content)
        # Summarize: first 200 chars or first meaningful line
        summary = content.strip()[:200].split("\n")[0].strip()[:200]

        doc = IngestedDoc(
            path=str(path),
            content=content,
            summary=summary,
            doc_type=doc_type,
            tags=tags,
            hash=h,
            ingested_at=datetime.now().isoformat(),
        )

        self.index[str(path)] = h
        self._save_index()
        return doc

    def ingest_directory(self, directory: str | Path, recursive: bool = True) -> list[IngestedDoc]:
        directory = Path(directory)
        if not directory.exists():
            return []

        docs = []
        pattern = "**/*" if recursive else "*"
        for f in sorted(directory.glob(pattern)):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                doc = self.ingest_file(f)
                if doc:
                    docs.append(doc)
        return docs

    def status(self) -> dict:
        return {
            "indexed_files": len(self.index),
            "kb_dir": str(self.kb_dir),
        }
