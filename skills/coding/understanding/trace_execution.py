import ast
import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class TraceExecutionSkill(BaseCodingSkill):
    name = "trace_execution"
    description = "Trace the call flow starting from a given function"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the source file"},
            "entry_point": {"type": "string", "description": "Function name where tracing starts"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["path", "entry_point"]

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        entry = kwargs.get("entry_point", "")
        if not path or not entry:
            return SkillResult(success=False, output="path and entry_point are required")
        fp = Path(path)
        if not fp.exists():
            return SkillResult(success=False, output=f"File not found: {path}")
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Read error: {e}")
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return SkillResult(success=False, output=f"Syntax error: {e}")

        # Build call graph
        calls = {}  # caller -> [callee]
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller = node.name
                callees = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            callees.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            callees.append(f"{child.func.attr}")
                if callees:
                    calls[caller] = callees

        # BFS from entry point
        visited = set()
        queue = [entry]
        trace = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            trace.append(current)
            for callee in calls.get(current, []):
                if callee not in visited:
                    queue.append(callee)

        if not trace:
            return SkillResult(success=False, output=f"Entry point '{entry}' not found or no calls traced")

        prompt = (
            f"Explain the execution flow starting from '{entry}' in {path}.\n"
            f"Call chain: {' → '.join(trace)}\n\n"
            f"Describe what each function does and how data flows between them."
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            explanation = resp["message"]["content"]
        except Exception as e:
            explanation = f"(LLM analysis unavailable: {e})"

        return SkillResult(
            success=True,
            output=explanation,
            data={"path": path, "entry_point": entry, "call_chain": trace},
        )
