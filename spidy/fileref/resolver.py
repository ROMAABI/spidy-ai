import os
from pathlib import Path
from typing import List


def resolve_file_refs(refs: list[Path]) -> list[dict]:
    results = []
    for path in refs:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            results.append({
                "path": str(path),
                "name": path.name,
                "content": content,
                "size": len(content),
            })
        except Exception as e:
            results.append({
                "path": str(path),
                "name": path.name,
                "content": f"[Error reading: {e}]",
                "size": 0,
            })
    return results


def inject_file_context(filerefs: list[dict]) -> str:
    if not filerefs:
        return ""
    parts = ["\n--- Referenced Files ---"]
    for ref in filerefs:
        parts.append(f"\n### {ref['name']} ({ref['path']})\n```\n{ref['content']}\n```")
    return "\n".join(parts)
