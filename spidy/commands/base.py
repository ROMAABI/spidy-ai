from dataclasses import dataclass, field


@dataclass
class CommandResult:
    output: str = ""
    success: bool = True
    data: dict = field(default_factory=dict)
    format: str = "text"


class BaseCommand:
    name: str = ""
    aliases: list = []
    description: str = ""
    usage: str = ""
    hidden: bool = False

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        raise NotImplementedError

    def help(self) -> str:
        return f"/{self.name} — {self.description}\n  Usage: {self.usage}"
