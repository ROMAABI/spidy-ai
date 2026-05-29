import ast
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class FindDeadCodeSkill(BaseCodingSkill):
    name = "find_dead_code"
    description = "Find unused variables, functions, and imports in a file"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the file to analyze"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["path"]

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        if not path:
            return SkillResult(success=False, output="No path provided")
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

        findings = []

        # Unused imports
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = node.lineno

        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                used_names.add(node.id)
            if isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Store):
                used_names.add(node.attr)

        for imp_name, line_no in imports.items():
            base_name = imp_name.split(".")[0]
            if base_name not in used_names:
                findings.append(f"Unused import: '{imp_name}' at line {line_no}")

        # Unused functions and classes defined in this file
        defined = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined[node.name] = ("function", node.lineno)
            elif isinstance(node, ast.ClassDef):
                defined[node.name] = ("class", node.lineno)

        for name, (kind, line_no) in defined.items():
            if name not in used_names and name != "__init__":
                findings.append(f"Unused {kind}: '{name}' at line {line_no}")

        # Unused variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id not in used_names and not target.id.startswith("_"):
                            findings.append(f"Possibly unused variable: '{target.id}' at line {node.lineno}")

        if not findings:
            findings.append("No dead code detected.")

        return SkillResult(success=True, output="\n".join(findings), data={"path": path, "findings": findings})
