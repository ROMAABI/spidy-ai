from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class SkillsCommand(BaseCommand):
    name = "skills"
    description = "List loaded skills and their triggers"
    usage = "/skills [category]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        try:
            from skills import ALL_SKILLS
        except Exception:
            return CommandResult(output="Skills module not available", success=False)
        if not ALL_SKILLS:
            return CommandResult(output="No skills loaded")
        lines = [f"Loaded {len(ALL_SKILLS)} skills:\n"]
        for skill in ALL_SKILLS[:30]:
            name = getattr(skill, "name", skill.__name__)
            desc = getattr(skill, "description", "")
            triggers = getattr(skill, "triggers", [])
            trigger_str = ", ".join(triggers[:5])
            t = f" ({trigger_str})" if trigger_str else ""
            lines.append(f"  {name:<20} {desc}{t}")
        if len(ALL_SKILLS) > 30:
            lines.append(f"  ... and {len(ALL_SKILLS) - 30} more")
        return CommandResult(output="\n".join(lines))

CommandRegistry.register(SkillsCommand())
