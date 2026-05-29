#!/usr/bin/env python3
"""
Spidy AI — Deeply System-Aware Personal Assistant

Modes:
  text     - CLI interactive mode
  tui      - Terminal UI via Textual
  diagnose - Full system health check
  snapshot - Collect/list/compare system snapshots
  doctor   - AI-powered health check with recommendations
  profile  - Display system hardware/OS/tool profile

Commands:
  python3 main.py diagnose [area]
  python3 main.py snapshot [take|list]
  python3 main.py doctor
  python3 main.py profile [show|tools]
  python3 main.py --ui tui
  python3 main.py [message]
"""
import sys
import os
import argparse


VENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
VENV_PYTHON = os.path.join(VENV, "bin", "python3")
if (
    "VIRTUAL_ENV" not in os.environ
    and os.path.exists(VENV_PYTHON)
    and sys.executable != VENV_PYTHON
):
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)


def main():
    parser = argparse.ArgumentParser(
        description="Spidy AI — Deeply System-Aware Personal Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--model", default="", help="Override default LLM model")
    parser.add_argument("--show-thinking", action="store_true",
                        help="Show AI thinking tokens")
    parser.add_argument("--ui", choices=["text", "tui"], default="text",
                        help="User interface mode (default: text)")

    # Commands
    parser.add_argument("command", nargs="?", default="",
                        help="Command: diagnose, snapshot, doctor, profile")
    parser.add_argument("subcommand", nargs="*",
                        help="Subcommand arguments")

    args = parser.parse_args()

    # ── CLI Commands ───────────────────────────────────────────────────────
    if args.command in ("diagnose", "diag"):
        _run_diagnose(args.subcommand)
        return
    if args.command == "snapshot":
        _run_snapshot(args.subcommand)
        return
    if args.command == "doctor":
        _run_doctor()
        return
    if args.command == "profile":
        _run_profile(args.subcommand)
        return
    if args.command == "rag":
        print(_run_rag(args.subcommand))
        return

    # ── Normal modes ──────────────────────────────────────────────────────
    if args.ui == "tui":
        _run_tui()
        return

    if args.command:
        _run_text_with_message(args)
    else:
        _run_text_interactive(args)


# ── CLI Command Handlers ─────────────────────────────────────────────────

def _run_diagnose(sub_args):
    from spidy.commands.diagnose import DiagnoseCommand
    area = sub_args[0] if sub_args else "all"
    print(DiagnoseCommand.run(area))


def _run_snapshot(sub_args):
    from spidy.commands.snapshot import SnapshotCommand
    cmd = SnapshotCommand()
    action = sub_args[0] if sub_args else "list"
    if action == "take":
        notes = " ".join(sub_args[1:]) if len(sub_args) > 1 else ""
        print(cmd.take(notes))
    elif action == "list":
        print(cmd.list())
    elif action == "compare" and len(sub_args) >= 3:
        print(cmd.compare(sub_args[1], sub_args[2]))
    else:
        print("Usage: python3 main.py snapshot [take|list|compare <a> <b>]")


def _run_doctor():
    from spidy.commands.doctor import DoctorCommand
    print(DoctorCommand.run())


def _run_profile(sub_args):
    from spidy.commands.profile import ProfileCommand
    fmt = sub_args[0] if sub_args else "show"
    if fmt == "json":
        print(ProfileCommand.json_output())
    elif fmt == "tools":
        print(ProfileCommand.tools())
    else:
        print(ProfileCommand.show())


def _run_rag(sub_args):
    from spidy.commands.rag import run as _rag_run
    return _rag_run(list(sub_args))


# ── Interactive Modes ────────────────────────────────────────────────────

def _run_tui():
    from spidy_tui.app import SpidyTUIApp
    app = SpidyTUIApp()
    app.run()


def _run_text_with_message(args):
    from core.assistant import Assistant
    assistant = Assistant(show_thinking=args.show_thinking)
    assistant.mode = "text"
    text = f"{args.command} {' '.join(args.subcommand)}"
    assistant.process(text)


def _run_text_interactive(args):
    from core.assistant import Assistant
    from spidy.profile import profile_summary, get_profile

    profile = get_profile()
    print(f"  Spidy AI — System-Aware Mode")
    print(f"  {profile_summary(profile)}")
    print()

    assistant = Assistant(show_thinking=args.show_thinking)
    assistant.mode = "text"

    if args.model:
        from core.brain import Brain
        if hasattr(assistant, "brain") and assistant.brain is not None:
            assistant.brain.model = args.model
            print(f"[Main] Model override: {args.model}")

    print("╔══════════════════════════════════════╗")
    print("║  Spidy AI — System-Aware Assistant   ║")
    print("║  Commands: diagnose, snapshot,       ║")
    print("║            doctor, profile            ║")
    print("╚══════════════════════════════════════╝")
    while True:
        try:
            text = input("\nYou: ").strip()
            if not text:
                continue
            if text.lower() in ("exit", "quit", "bye"):
                print("Goodbye!")
                break
            # Inline CLI commands
            parts = text.split()
            if parts[0] in ("diagnose", "diag"):
                _run_diagnose(parts[1:])
                continue
            if parts[0] == "snapshot":
                _run_snapshot(parts[1:])
                continue
            if parts[0] == "doctor":
                _run_doctor()
                continue
            if parts[0] == "profile":
                _run_profile(parts[1:])
                continue
            if parts[0] == "rag":
                print(_run_rag(parts[1:]))
                continue
            assistant.process(text)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
