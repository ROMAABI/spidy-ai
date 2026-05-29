import ast
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class DetectCodeSmellsSkill(BaseCodingSkill):
    name = "detect_code_smells"
    description = "Analyze a file for anti-patterns, long functions, deep nesting, magic numbers"

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

        issues = []

        # 1. Long functions (> 50 lines)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines = (node.end_lineno or node.lineno) - node.lineno
                if lines > 50:
                    issues.append(f"Long function: '{node.name}' ({lines} lines, line {node.lineno})")

        # 2. Deep nesting (> 4 levels)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                max_depth = self._nesting_depth(node)
                if max_depth > 4:
                    issues.append(f"Deep nesting in '{node.name}' (depth {max_depth}, line {node.lineno})")

        # 3. Too many parameters (> 5)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                n_params = len(node.args.args)
                if n_params > 5:
                    issues.append(f"Too many params in '{node.name}' ({n_params}, line {node.lineno})")

        # 4. Magic numbers
        magic = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if not isinstance(node.value, bool) and node.value not in (0, 1, -1, 100):
                    magic.append(f"Magic number {node.value} at line {node.lineno}")
        if len(magic) > 3:
            issues.append(f"Magic numbers ({len(magic)} found, e.g. {magic[0]})")

        # 5. Empty except blocks
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None and not node.body:
                issues.append(f"Bare empty except at line {node.lineno}")

        # 6. Too many global variables
        globals_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Global))
        if globals_count > 3:
            issues.append(f"Excessive use of 'global' ({globals_count} occurrences)")

        if not issues:
            issues.append("No significant code smells detected.")

        return SkillResult(
            success=True,
            output="\n".join(issues),
            data={"path": path, "issue_count": len(issues), "issues": issues},
        )

    @staticmethod
    def _nesting_depth(node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)):
                child_depth = DetectCodeSmellsSkill._nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth
