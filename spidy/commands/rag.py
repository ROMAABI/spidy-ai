"""
spidy/commands/rag.py  –  CLI command to ingest/query the RAG knowledge base.

Usage:
    python3 main.py rag ingest [--recursive] <path>
    python3 main.py rag status
    python3 main.py rag query <text>
"""
import sys
from pathlib import Path


def run(args: list[str]) -> str:
    """Dispatch RAG subcommands."""
    if not args:
        return status()
    sub = args[0]
    if sub == "ingest":
        return _ingest(args[1:])
    if sub == "status":
        return status()
    if sub == "query":
        return _query(args[1:])
    return f"Unknown rag subcommand: {sub}. Try: ingest, status, query"


# ── Default search paths ──────────────────────────────────────────────────
DEFAULT_PATHS = [
    Path.home() / ".config",
    Path.home() / ".local/share/spidy/knowledge",
    Path.home() / "notes",
    Path.home() / "Documents",
    Path("/var/log"),
]


def _ingest(sub_args: list[str]) -> str:
    """Ingest files from one or more directories."""
    from spidy.rag.ingester import KnowledgeIngester
    ingester = KnowledgeIngester()
    paths = [Path(a) for a in sub_args if not a.startswith("--")]
    recursive = "--recursive" in sub_args or "-r" in sub_args

    if not paths:
        paths = DEFAULT_PATHS

    total = 0
    all_docs: list = []
    lines = []
    for p in paths:
        if not p.exists():
            lines.append(f"  SKIP  {p}  (not found)")
            continue
        if p.is_file():
            doc = ingester.ingest_file(p)
            if doc:
                total += 1
                all_docs.append(doc)
                lines.append(f"  OK    {p}  ({doc.doc_type})")
            else:
                lines.append(f"  SAME  {p}  (unchanged or unsupported)")
        else:
            docs = ingester.ingest_directory(p, recursive=recursive)
            if docs:
                total += len(docs)
                all_docs.extend(docs)
                for d in docs[:20]:
                    lines.append(f"  OK    {d.path}  ({d.doc_type})")
                if len(docs) > 20:
                    lines.append(f"  ... and {len(docs) - 20} more")
            else:
                lines.append(f"  NONE  {p}  (no new files)")

    # Push to ChromaDB
    if all_docs:
        from spidy.rag.retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        pushed = retriever.add_documents(all_docs)
        lines.append(f"  Vector: {pushed} document(s) added to ChromaDB")

    header = f"Ingested {total} new document(s)\n"
    return header + "\n".join(lines)


def status() -> str:
    """Show RAG knowledge base status."""
    try:
        from spidy.rag.ingester import KnowledgeIngester
        ingester = KnowledgeIngester()
        st = ingester.status()
    except Exception as exc:
        return f"RAG status unavailable: {exc}"

    # Count docs in ChromaDB if available
    chroma_count = 0
    try:
        from spidy.rag.retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        if retriever.chroma and retriever.chroma is not False:
            chroma_count = retriever.chroma.count()
    except Exception:
        pass

    return (
        f"Knowledge Base Status\n"
        f"  Indexed files : {st['indexed_files']}\n"
        f"  Vector docs   : {chroma_count}\n"
        f"  KB directory  : {st['kb_dir']}\n"
        f"  Chroma path   : {Path.home() / '.cache/spidy/chroma'}\n"
    )


def _query(sub_args: list[str]) -> str:
    """Query the knowledge base."""
    if not sub_args:
        return "Usage: python3 main.py rag query <text>"

    query_text = " ".join(sub_args)
    try:
        from spidy.rag.retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        docs = retriever.search(query_text, n=5)
    except Exception as exc:
        return f"Query failed: {exc}"

    if not docs:
        return f"No results found for: {query_text}"

    lines = [f"Results for: {query_text}"]
    for i, d in enumerate(docs, 1):
        lines.append(f"\n[{i}] from {d.source}  (score: {d.score:.2f})")
        lines.append(f"    {d.content[:200]}...")
    return "\n".join(lines)
