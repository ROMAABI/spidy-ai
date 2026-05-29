#!/bin/bash
source /home/spix/spidy-ai/venv/bin/activate
cd /home/spix/spidy-ai

# Launch the Textual TUI
python3 main.py --ui tui "$@"
