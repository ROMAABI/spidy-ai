"""
spidy/rag/retriever.py — Knowledge retrieval from the vector store.
"""

import json
from pathlib import Path
import subprocess
from dataclasses import dataclass, field


@dataclass
class RetrievedDoc:
    content: str = ""
    source: str = ""
    score: float = 0.0
    doc_type: str = ""


class KnowledgeRetriever:
    """Retrieve relevant knowledge from ingested docs and vector DB."""

    def __init__(self, chroma_path: str = "", kb_dir: str = ""):
        self.kb_dir = Path(kb_dir or Path.home() / ".local/share/spidy/knowledge")
        self.chroma_path = chroma_path or str(Path.home() / ".cache/spidy/chroma")
        self._chroma = None

    @property
    def chroma(self):
        if self._chroma is None:
            try:
                import chromadb
                client = chromadb.PersistentClient(path=self.chroma_path)
                self._chroma = client.get_or_create_collection("spidy_knowledge")
            except Exception:
                self._chroma = False
        return self._chroma

    def add_documents(self, docs: list) -> int:
        """Bulk-add IngestedDoc objects to ChromaDB.

        Returns the number of documents successfully added.
        """
        if not self.chroma or self.chroma is False:
            return 0
        added = 0
        for doc in docs:
            text = doc.content or doc.summary
            if not text.strip():
                continue
            try:
                self.chroma.add(
                    documents=[text],
                    metadatas=[{
                        "source": doc.path,
                        "type": doc.doc_type,
                        "tags": ",".join(doc.tags) if doc.tags else "",
                    }],
                    ids=[doc.hash],
                )
                added += 1
            except Exception:
                continue
        return added

    def search(self, query: str, n: int = 5) -> list[RetrievedDoc]:
        results = []

        # 1. Vector search via ChromaDB
        if self.chroma and self.chroma is not False:
            try:
                vec_results = self.chroma.query(query_texts=[query], n_results=n)
                if vec_results and vec_results.get("documents"):
                    for i, doc in enumerate(vec_results["documents"][0]):
                        meta = (vec_results.get("metadatas") or [{}])[0][i] if vec_results.get("metadatas") else {}
                        results.append(RetrievedDoc(
                            content=doc[:500],
                            source=meta.get("source", "vector_db"),
                            score=1.0 - (i * 0.1),
                            doc_type=meta.get("type", ""),
                        ))
            except Exception:
                pass

        # 2. Keyword (grep) fallback on knowledge base files
        if self.kb_dir.exists():
            try:
                r = subprocess.run(
                    ["grep", "-ril", query, str(self.kb_dir)],
                    capture_output=True, text=True, timeout=10,
                )
                if r.stdout.strip():
                    files = r.stdout.strip().splitlines()[:n]
                    for f in files:
                        try:
                            content = Path(f).read_text(encoding="utf-8", errors="ignore")[:500]
                            results.append(RetrievedDoc(
                                content=content,
                                source=f,
                                score=0.5,
                                doc_type=Path(f).suffix,
                            ))
                        except Exception:
                            pass
            except Exception:
                pass

        return results

    def add_documents(self, docs: list) -> int:
        """Bulk-add ingested docs to vector DB."""
        if not self.chroma or self.chroma is False:
            return 0
        documents = []
        metadatas = []
        ids = []
        import hashlib
        for doc in docs:
            if not doc.content.strip():
                continue
            documents.append(doc.content)
            metadatas.append({
                "source": doc.path,
                "type": doc.doc_type,
                "tags": ",".join(doc.tags),
                "ingested": doc.ingested_at,
            })
            ids.append(hashlib.md5(doc.path.encode()).hexdigest())
        if documents:
            self.chroma.add(documents=documents, metadatas=metadatas, ids=ids)
        return len(documents)

    def count(self) -> int:
        if self.chroma and self.chroma is not False:
            try:
                return self.chroma.count()
            except Exception:
                pass
        return 0
