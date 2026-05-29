import asyncio
from pathlib import Path
from skills.coding.base import SkillResult, BaseCodingSkill


class ExplainProjectStructureSkill(BaseCodingSkill):
    name = "explain_project_structure"
    description = "Walk a directory tree and explain the architecture"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "root": {"type": "string", "description": "Root directory of the project"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["root"]

    async def execute(self, **kwargs) -> SkillResult:
        root = kwargs.get("root", "")
        if not root:
            return SkillResult(success=False, output="No root path provided")
        rp = Path(root)
        if not rp.exists():
            return SkillResult(success=False, output=f"Directory not found: {root}")
        if not rp.is_dir():
            return SkillResult(success=False, output=f"Not a directory: {root}")

        tree_lines = []
        tree_lines.append(f"Project: {rp.resolve()}")
        tree_lines.append("")

        ignore = {".git", "__pycache__", ".venv", "venv", "node_modules", ".tox", ".egg-info", "dist", "build", ".mypy_cache", ".pytest_cache"}

        for child in sorted(rp.iterdir()):
            self._render_tree(child, "", tree_lines, ignore)

        tree_str = "\n".join(tree_lines)

        prompt = (
            f"Analyze the project structure rooted at {rp.resolve()} and explain the architecture.\n\n"
            f"Directory tree:\n{tree_str}\n\n"
            f"Describe: what kind of project this is, the role of each top-level module/directory, "
            f"and how the components likely interact."
        )
        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            analysis = resp["message"]["content"]
        except Exception as e:
            analysis = f"(LLM analysis unavailable: {e})"

        return SkillResult(
            success=True,
            output=f"{tree_str}\n\n{analysis}",
            data={"root": str(rp.resolve()), "tree": tree_str},
        )

    @staticmethod
    def _render_tree(path: Path, prefix: str, lines: list, ignore: set) -> None:
        if path.name in ignore:
            return
        if path.is_dir():
            lines.append(f"{prefix}📁 {path.name}/")
            for child in sorted(path.iterdir()):
                ExplainProjectStructureSkill._render_tree(child, prefix + "    ", lines, ignore)
        else:
            lines.append(f"{prefix}📄 {path.name}")
