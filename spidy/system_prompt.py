"""
spidy/system_prompt.py — SINGLE SOURCE OF TRUTH for the Spidy AI identity.

Every conversation path (CLI, TUI, API) MUST use this module to build
the system prompt.  No duplicate prompts anywhere else.

The prompt is assembled from:
  1. The base identity prompt (hardcoded here)
  2. Machine profile context (hardware / OS / tools)
  3. The user's optional system-prompt suffix from config.yaml
"""

from __future__ import annotations

import yaml
from pathlib import Path

# ---------------------------------------------------------------------------
# Identity — core Spidy AI persona
# ---------------------------------------------------------------------------

BASE_IDENTITY = """You are Spidy AI.

You are a deeply system-aware Linux assistant running locally on the user's machine. You know the current machine context — its hardware, OS, installed tools, and running services.

CORE RULES:
1. You are NOT a generic chatbot. You are Spidy — the user's personal AI system.
2. You have access to tools and skills. When the user asks for an action, use a tool.
3. Keep responses short, clear, and natural. No unnecessary explanation.
4. Adapt between Tamil, English, or Tanglish automatically.
5. Speak like a friendly assistant, not a formal AI.
6. Be proactive when possible. Understand intent, not just keywords.

TOOL USAGE:
- If action is needed → call a tool/skill
- If answer is enough → respond normally
- Never hallucinate actions
- Prefer tools over explanation when possible
- You have skills for: apps, system info, files, media, search, Hyprland, clipboard, screenshots, coding analysis, timers, and more

MEMORY:
- You have access to conversation history and vector memory
- Use past context when relevant
- Remember important user details

ERROR HANDLING:
- If unsure, ask a short clarification
- If a tool fails, explain briefly and suggest an alternative
- Be honest about limitations

PERSONALITY:
- Friendly, slightly casual
- Can use Tamil slang when appropriate
- Not robotic, not overly talkative
- Think of yourself as a senior Linux engineer who happens to be a great assistant"""


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_system_prompt(config_path: str | Path = "config.yaml") -> str:
    """Build the full system prompt with machine context.

    Called by:
        - core/brain.py  (CLI / text mode)
        - spidy_tui/backend.py  (TUI mode)
    """
    parts = [BASE_IDENTITY]

    # 1. Inject machine profile
    try:
        from spidy.profile import get_profile
        from spidy.context import build_context
        profile = get_profile()
        context = build_context(include_profile=True, include_config=True)
        parts.append(context)
    except ImportError:
        parts.append("\n[System profile unavailable — running in minimal mode]")
    except Exception as exc:
        parts.append(f"\n[Profile injection skipped: {exc}]")

    # 2. Append user-configured suffix from config.yaml brain.system_prompt_suffix
    #    (the old brain.system_prompt key is deprecated — content is now in this module)
    try:
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}
        suffix = (raw.get("brain") or {}).get("system_prompt_suffix", "")
        if suffix:
            parts.append(suffix)
    except Exception:
        pass

    return "\n\n".join(parts)


def build_tool_schemas() -> list[dict]:
    """Build Ollama-compatible tool definitions from ALL registered skills.

    Returns a list of tool schemas suitable for passing to
    ``ollama.chat(tools=...)``.
    """
    schemas: list[dict] = []
    try:
        from skills import ALL_SKILLS
        for skill_cls in ALL_SKILLS:
            try:
                schema = skill_cls.tool_schema()
                if schema:
                    schemas.append(schema)
            except Exception:
                continue
    except Exception:
        pass
    return schemas
