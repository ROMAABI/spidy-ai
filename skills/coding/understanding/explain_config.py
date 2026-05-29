from pathlib import Path
import asyncio
from skills.coding.base import SkillResult, BaseCodingSkill


class ExplainConfigSkill(BaseCodingSkill):
    name = "explain_config"
    description = "Read and explain a config file (yaml/toml/json/ini)"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "path": {"type": "string", "description": "Path to the config file"},
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

        suffix = fp.suffix.lower()
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            return SkillResult(success=False, output=f"Read error: {e}")

        parsed = None
        parse_error = None
        if suffix in (".yaml", ".yml"):
            try:
                import yaml
                parsed = yaml.safe_load(content)
            except Exception as e:
                parse_error = f"YAML parse error: {e}"
        elif suffix == ".json":
            import json
            try:
                parsed = json.loads(content)
            except Exception as e:
                parse_error = f"JSON parse error: {e}"
        elif suffix == ".toml":
            try:
                import tomllib
                parsed = tomllib.loads(content)
            except Exception:
                import tomli
                try:
                    parsed = tomli.loads(content)
                except Exception as e:
                    parse_error = f"TOML parse error: {e}"
        elif suffix == ".ini":
            try:
                from configparser import ConfigParser
                cp = ConfigParser()
                cp.read_string(content)
                parsed = {s: dict(cp[s]) for s in cp.sections()}
            except Exception as e:
                parse_error = f"INI parse error: {e}"
        else:
            parse_error = f"Unsupported config format: {suffix}"

        parts = []
        parts.append(f"Config file: {fp.name}")
        parts.append(f"Format: {suffix}")
        parts.append(f"Size: {len(content)} bytes")
        parts.append("")

        if parse_error:
            parts.append(parse_error)
        elif parsed is not None:
            parts.append("Parsed content:")
            import json
            parts.append(json.dumps(parsed, indent=2, default=str))
            parts.append("")

            try:
                import ollama
                resp = await asyncio.to_thread(
                    ollama.chat,
                    model="kimi-k2",
                    messages=[{"role": "user", "content": f"Explain what this {suffix} config file does. Describe the purpose of each top-level key.\n\n```yaml\n{json.dumps(parsed, indent=2, default=str)[:3000]}\n```"}],
                    stream=False,
                )
                explanation = resp["message"]["content"]
            except Exception as e:
                explanation = f"(LLM unavailable: {e})"

            parts.append(explanation)

        return SkillResult(success=parse_error is None, output="\n".join(parts), data={"path": path, "parsed": parsed})
