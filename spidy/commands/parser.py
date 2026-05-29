"""
spidy/commands/parser.py — Unified parser for slash commands, agent modes, shell, file refs.

In one pass, this parses a user message and returns a structured result:

  ParsedMessage
    ├── type: "slash" | "mode" | "shell" | "fileref" | "chat"
    ├── command / mode / shell_cmd / filerefs
    ├── args / text
    └── filerefs (file references anywhere in message)
"""
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class ParsedMessage:
    type: Literal["slash", "mode", "shell", "fileref", "chat"] = "chat"
    # Slash command
    command: str = ""
    args: list[str] = field(default_factory=list)
    # Agent mode
    mode: str = ""
    # Shell command
    shell_cmd: str = ""
    # File references (anywhere in message)
    filerefs: list[Path] = field(default_factory=list)
    # Clean text after removing all special syntax
    clean_text: str = ""
    raw_text: str = ""


# ── Resolve @file references ──────────────────────────────────────────────

_FILE_REF_RE = re.compile(r"@([\w./\\_-]+(?:\.[\w]+)?)")


def parse(text: str, cwd: str | None = None) -> ParsedMessage:
    text_stripped = text.strip()
    if not text_stripped:
        return ParsedMessage(raw_text=text)

    result = ParsedMessage(raw_text=text)

    # ── 1. Agent mode (@plan, @build, …) ──────────────────────────────
    mode_match = re.match(r"^@(\w+)\s*(.*)", text_stripped, re.DOTALL)
    if mode_match:
        result.type = "mode"
        result.mode = mode_match.group(1).lower()
        text_stripped = mode_match.group(2).strip()

    # ── 2. Slash command (/help, /init …) ─────────────────────────────
    slash_match = re.match(r"^/(\w+)\s*(.*)", text_stripped, re.DOTALL)
    if slash_match:
        result.type = "slash"
        result.command = slash_match.group(1).lower()
        raw_args = slash_match.group(2).strip()
        result.args = shlex.split(raw_args) if raw_args else []
        text_stripped = raw_args

    # ── 3. Shell command (!pwd, !ls …) ────────────────────────────────
    shell_match = re.match(r"^!(.+)$", text_stripped, re.DOTALL)
    if shell_match and result.type == "chat":
        result.type = "shell"
        result.shell_cmd = shell_match.group(1).strip()
        text_stripped = ""

    # ── 4. File references (@README.md) ───────────────────────────────
    filerefs: list[Path] = []
    cwd_path = Path(cwd) if cwd else Path.cwd()

    for match in _FILE_REF_RE.finditer(text_stripped):
        ref = match.group(1)
        # Skip common false positives (URLs, emails)
        if ref.startswith("http") or "@" in ref and "." not in ref.split("@")[-1]:
            continue
        candidate = cwd_path / ref
        if candidate.exists() and candidate.is_file():
            filerefs.append(candidate.resolve())

    result.filerefs = filerefs
    result.clean_text = text_stripped
    return result
