from spidy.commands.base import BaseCommand, CommandResult


class CommandRegistry:
    _commands: dict[str, BaseCommand] = {}
    _aliases: dict[str, str] = {}

    @classmethod
    def register(cls, cmd: BaseCommand) -> None:
        cls._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            cls._aliases[alias] = cmd.name

    @classmethod
    def get(cls, name: str) -> BaseCommand | None:
        resolved = cls._aliases.get(name, name)
        return cls._commands.get(resolved)

    @classmethod
    def all(cls) -> list[BaseCommand]:
        return list(cls._commands.values())

    @classmethod
    def visible(cls) -> list[BaseCommand]:
        return [c for c in cls._commands.values() if not c.hidden]

    @classmethod
    def autocomplete(cls, prefix: str) -> list[str]:
        return [f"/{n}" for n in cls._commands if n.startswith(prefix)]

    @classmethod
    async def dispatch(cls, name: str, args: list[str],
                       context: dict | None = None) -> CommandResult:
        cmd = cls.get(name)
        if cmd is None:
            return CommandResult(output=f"Unknown command: /{name}", success=False)
        return await cmd.run(args, context or {})
