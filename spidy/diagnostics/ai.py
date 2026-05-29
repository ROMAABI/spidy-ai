"""
spidy/diagnostics/ai.py — AI/LLM infrastructure diagnostics.
"""

import subprocess
from dataclasses import dataclass, field


@dataclass
class AIDiagResult:
    ollama_running: bool = False
    ollama_version: str = ""
    models_installed: list = field(default_factory=list)
    model_details: list = field(default_factory=list)
    default_model_size: str = ""
    rag_available: bool = False
    chromadb_available: bool = False
    vector_count: int = 0
    total_inference_ram_gb: float = 0.0


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception:
        return ""


class AIDiagnostics:
    """Check AI infrastructure: Ollama health, models, RAG readiness."""

    @staticmethod
    def diagnose() -> AIDiagResult:
        r = AIDiagResult()

        # Ollama running?
        r.ollama_running = _run("pgrep ollama") != ""

        # Version
        r.ollama_version = _run("ollama --version 2>/dev/null")

        # Models
        out = _run("ollama list 2>/dev/null")
        if out:
            lines = out.splitlines()[1:]  # skip header
            for line in lines:
                parts = line.split()
                if parts:
                    r.models_installed.append(parts[0])
                    if len(parts) >= 3:
                        r.model_details.append({"name": parts[0], "size": parts[2]})

        if r.model_details:
            r.default_model_size = r.model_details[0].get("size", "")

        # ChromaDB
        try:
            import chromadb
            r.chromadb_available = True
            client = chromadb.PersistentClient(path=str(subprocess.run(
                ["python3", "-c", "import yaml; print(yaml.safe_load(open('config.yaml'))['memory']['chroma_path'])"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip() or "/tmp/spidy_chroma"))
            try:
                coll = client.get_collection("spidy_memory")
                r.vector_count = coll.count()
            except Exception:
                pass
        except ImportError:
            r.chromadb_available = False

        # RAG
        r.rag_available = r.chromadb_available and len(r.models_installed) > 0

        # Estimate RAM usage from model sizes
        for detail in r.model_details:
            size_str = detail.get("size", "0B")
            if "GB" in size_str:
                try:
                    r.total_inference_ram_gb += float(size_str.replace("GB", "").strip())
                except ValueError:
                    pass

        return r

    @staticmethod
    def summary(diag: AIDiagResult | None = None) -> str:
        if diag is None:
            diag = AIDiagnostics.diagnose()
        lines = [
            f"Ollama: {'running' if diag.ollama_running else 'STOPPED'} v{diag.ollama_version}",
            f"Models: {', '.join(diag.models_installed[:5]) or 'none'}",
            f"Estimated inference RAM: {diag.total_inference_ram_gb:.1f} GB",
            f"Vector DB: {'chromadb active' if diag.chromadb_available else 'not configured'} ({diag.vector_count} vectors)",
        ]
        if not diag.ollama_running:
            lines.append("\nACTION: Start Ollama with: systemctl --user start ollama")
        if diag.total_inference_ram_gb > 12:
            lines.append("\nNOTE: Total model sizes exceed available RAM (16GB). Consider smaller quantized models.")
        return "\n".join(lines)
