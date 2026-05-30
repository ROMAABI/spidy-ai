#!/usr/bin/env python3
"""
Generate documentation screenshots for Spidy AI.

Run this script to create placeholder screenshots for the README.
Actual screenshots should be captured from the running TUI.

Usage:
    python3 docs/generate-screenshots.py
"""

import os
from pathlib import Path

DOCS_DIR = Path(__file__).parent
SCREENSHOTS_DIR = DOCS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def create_placeholder(name: str, title: str, lines: list[str]) -> None:
    """Create a placeholder screenshot file with ASCII art."""
    filepath = SCREENSHOTS_DIR / f"{name}.txt"
    width = 70
    border = "─" * (width - 2)

    content = f"┌{border}┐\n"
    content += f"│ {title:^{width - 4}} │\n"
    content += f"├{border}┤\n"
    for line in lines:
        content += f"│ {line:<{width - 4}} │\n"
    content += f"└{border}┘\n"

    filepath.write_text(content)
    print(f"  Created: {filepath}")


def main() -> None:
    print("Generating Spidy AI documentation screenshots...\n")

    # Main UI
    create_placeholder(
        "main-ui",
        "Spidy AI — Main Interface",
        [
            "",
            "  YOU  12:35 PM                           ",
            "  ┌─────────────────────────────────────┐",
            "  │ open firefox                         │",
            "  └─────────────────────────────────────┘",
            "",
            "  SPIDY  12:35 PM                       ",
            "  ┌─────────────────────────────────────┐",
            "  │ Opening Firefox.                     │",
            "  └─────────────────────────────────────┘",
            "",
            "  ┌─────────────────────────────────────┐",
            "  │ YOU  12:36 PM                        │",
            "  │ how's my RAM                         │",
            "  └─────────────────────────────────────┘",
            "",
            "  ┌─────────────────────────────────────┐",
            "  │ SPIDY  12:36 PM                     │",
            "  │ RAM: 34% used (5.2 GB / 15.3 GB)   │",
            "  │ CPU: 12%  │  Disk: 45%  │  Up: 3d   │",
            "  └─────────────────────────────────────┘",
            "",
            "  ▸ Type a message...                   ",
            "",
        ],
    )

    # Voice Mode
    create_placeholder(
        "voice-mode",
        "Spidy AI — Voice Mode",
        [
            "",
            "  🎤 VOICE MODE ACTIVE",
            "",
            "  Wake word: SPIDY",
            "  Status: Listening...",
            "",
            "  ┌─────────────────────────────────────┐",
            "  │ \"Hey Spidy, play some music\"        │",
            "  └─────────────────────────────────────┘",
            "",
            "  SPIDY: Opening Spotify.",
            "         Starting playback...",
            "",
            "  [████████████████░░░░] 78% volume",
            "",
        ],
    )

    # Skills
    create_placeholder(
        "skills",
        "Spidy AI — Skills Execution",
        [
            "",
            "  YOU: set a reminder for 3pm",
            "",
            "  SPIDY: ✓ Reminder set for 3:00 PM today.",
            "",
            "  YOU: find large files in Downloads",
            "",
            "  SPIDY: Found 3 large files:",
            "         • movie.mkv     (4.2 GB)",
            "         • backup.tar.gz (1.8 GB)",
            "         • dataset.zip   (950 MB)",
            "",
            "  YOU: add todo buy groceries",
            "",
            "  SPIDY: ✓ Added to todo list:",
            "         [ ] Buy groceries",
            "",
        ],
    )

    # Themes
    create_placeholder(
        "themes",
        "Spidy AI — Theme Engine",
        [
            "",
            "  ┌─── DARK THEME ──────────────────────┐",
            "  │ Background:  #1a1b26                 │",
            "  │ Primary:     #7aa2f7                 │",
            "  │ Accent:      #bb9af7                 │",
            "  │ Text:        #c0caf5                 │",
            "  └─────────────────────────────────────┘",
            "",
            "  ┌─── LIGHT THEME ─────────────────────┐",
            "  │ Background:  #f5f5f5                 │",
            "  │ Primary:     #1a6b37                 │",
            "  │ Accent:      #6b3fa0                 │",
            "  │ Text:        #333333                 │",
            "  └─────────────────────────────────────┘",
            "",
            "  Toggle: Ctrl+T or /theme",
            "",
        ],
    )

    # Context Panel
    create_placeholder(
        "context-panel",
        "Spidy AI — Context Panel",
        [
            "",
            "  ┌─── CONTEXT ─────────────────────────┐",
            "  │ [goal:active]                        │",
            "  │ Build Spidy AI                       │",
            "  │ TTS: Speaking  Queue: 0              │",
            "  │                                      │",
            "  │ [model:status]                       │",
            "  │ Active  deepseek-chat-v3-0324        │",
            "  │ Provider OpenRouter                  │",
            "  │ Speed   45.2 t/s                     │",
            "  │ Network Online                       │",
            "  │                                      │",
            "  │ [tts:status]                         │",
            "  │ Engine  gTTS                         │",
            "  │ Volume  85%                          │",
            "  │ State   Speaking                     │",
            "  │                                      │",
            "  │ [git:status]                         │",
            "  │ Branch  main                         │",
            "  │ Uncommitted  3                       │",
            "  │ Last Commit  fix: TTS streaming      │",
            "  │                                      │",
            "  │ [system:health]                      │",
            "  │ CPU  ████░░░░ 23%                    │",
            "  │ RAM  ██████░░ 67%                    │",
            "  │ Disk ███████░ 89%                    │",
            "  │ Up   3d 12h 45m                      │",
            "  └─────────────────────────────────────┘",
            "",
        ],
    )

    print(f"\n✅ Screenshots generated in {SCREENSHOTS_DIR}")
    print("   Replace these placeholders with actual TUI screenshots.")
    print("   Run: python3 main.py --ui tui")
    print("   Then capture screenshots with your preferred tool.")


if __name__ == "__main__":
    main()
