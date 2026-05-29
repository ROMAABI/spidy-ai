from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry
from spidy.agents import MODE_REGISTRY, get_mode

class AgentCommand(BaseCommand):
    name = "agent"
    aliases = ["mode"]
    description = "Switch agent mode (@plan, @build, @general, @system, @research)"
    usage = "/agent [mode]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        if not args:
            lines = ["Available modes:\n"]
            for m in MODE_REGISTRY.values():
                lines.append(f"  @{m.name:<12} {m.description}")
            lines.append("\nUsage: /agent <mode> or @<mode> <message>")
            return CommandResult(output="\n".join(lines))
        mode_name = args[0].lower()
        mode = get_mode(mode_name)
        if not mode:
            return CommandResult(output=f"Unknown mode: {mode_name}. Available: {', '.join(MODE_REGISTRY.keys())}", success=False)
        assistant = (context or {}).get("assistant")
        if assistant:
            assistant.active_mode = mode
        return CommandResult(output=f"Switched to @{mode.name} mode\n{mode.description}")

CommandRegistry.register(AgentCommand())
