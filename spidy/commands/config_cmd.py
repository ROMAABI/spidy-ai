import yaml
from pathlib import Path
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ConfigCommand(BaseCommand):
    name = "config"
    aliases = ["cfg", "settings"]
    description = "View configuration"
    usage = "/config [set key=value]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        config_path = Path("config.yaml")
        if not config_path.exists():
            return CommandResult(output="config.yaml not found", success=False)
        cfg = yaml.safe_load(config_path.read_text())
        if not args:
            from spidy.profile import get_profile
            profile = get_profile()
            lines = [f"  Model      : {cfg.get('brain', {}).get('cloud_model', '?')}"]
            lines.append(f"  Provider   : Ollama (local)")
            os_info = profile.os
            lines.append(f"  Os         : {getattr(os_info, 'distro', '?')}")
            lines.append(f"  Desktop    : {getattr(os_info, 'desktop', '?')}")
            return CommandResult(output="Configuration:\n" + "\n".join(lines))
        if args[0] == "set" and len(args) >= 2:
            return CommandResult(output=f"Would set: {args[1]} (config editing not yet implemented)")
        return CommandResult(output=f"Usage: /config or /config set key=value")

CommandRegistry.register(ConfigCommand())
