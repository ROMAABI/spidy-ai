from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AgentMode:
    name: str
    description: str
    read_only: bool = False
    allowed_tools: list[str] = field(default_factory=lambda: ["*"])
    system_prompt_suffix: str = ""


MODE_REGISTRY: dict[str, AgentMode] = {
    "plan": AgentMode(
        name="plan",
        description="Read-only planning and analysis — no file modifications",
        read_only=True,
        allowed_tools=["read", "search", "grep", "list"],
        system_prompt_suffix="You are in PLAN mode. Analyze and plan only. Do NOT modify any files.",
    ),
    "build": AgentMode(
        name="build",
        description="Full implementation mode — can modify files and execute tools",
        read_only=False,
        system_prompt_suffix="You are in BUILD mode. You can create and modify files as needed.",
    ),
    "general": AgentMode(
        name="general",
        description="Standard chat mode",
        read_only=False,
        system_prompt_suffix="",
    ),
    "system": AgentMode(
        name="system",
        description="Linux system administration mode — diagnostic and control commands",
        read_only=False,
        allowed_tools=["*"],
        system_prompt_suffix="You are in SYSTEM mode. You have access to system administration commands and diagnostics.",
    ),
    "research": AgentMode(
        name="research",
        description="Deep research mode — analyze repositories and codebases",
        read_only=True,
        allowed_tools=["read", "search", "grep", "list", "explore", "librarian"],
        system_prompt_suffix="You are in RESEARCH mode. Explore and analyze deeply. Do NOT modify files.",
    ),
}


def get_mode(name: str) -> AgentMode | None:
    return MODE_REGISTRY.get(name.lower())
