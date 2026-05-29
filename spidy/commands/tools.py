from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ToolsCommand(BaseCommand):
    name = "tools"
    description = "List available tools and executor commands"
    usage = "/tools"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        try:
            from tools.executor import Executor
            tools_info = ["  executor - Command execution with confirmation"]
        except Exception:
            tools_info = []
        try:
            from tools.base_tool import BaseTool
            tools_info.append("  base_tool - Tool calling framework")
        except Exception:
            pass
        lines = ["Available tools:\n"]
        lines.extend(tools_info)
        lines.append("\nSlash commands available via /help")
        return CommandResult(output="\n".join(lines))

CommandRegistry.register(ToolsCommand())
