"""
spidy - System-Aware Personal AI Assistant Engine.

Spidy is NOT a generic chatbot. It's a deeply system-aware
personal AI operating layer optimized for:
  - Arch Linux / EndeavourOS
  - Hyprland / Wayland
  - Local LLMs (Ollama)
  - Terminal-first workflows
"""

from spidy.profile import SystemProfile
from spidy.config import load_config
from spidy.context import build_context
from spidy.logger import get_logger

__version__ = "0.1.0"
