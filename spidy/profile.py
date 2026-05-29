"""
spidy/profile.py — System Profile: hardware, OS, installed tools, configs.

Discovers and caches system information so Spidy understands
the specific machine without hardcoded assumptions.
"""

import os
import re
import json
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class HardwareInfo:
    cpu: str = ""
    cores: int = 0
    threads: int = 0
    ram_gb: float = 0.0
    gpu: str = ""
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0


@dataclass
class OSInfo:
    distro: str = ""
    kernel: str = ""
    desktop: str = ""
    display_server: str = ""
    shell: str = ""
    terminal: str = ""


@dataclass
class ToolInfo:
    ollama: bool = False
    git: bool = False
    python: str = ""
    node: str = ""
    docker: bool = False
    yay: bool = False
    paru: bool = False
    neovim: bool = False
    htop: bool = False
    btop: bool = False
    lazygit: bool = False
    lazyvim: bool = False
    tmux: bool = False
    zoxide: bool = False
    fzf: bool = False
    fd: bool = False
    ripgrep: bool = False
    eza: bool = False
    bat: bool = False
    jq: bool = False
    yt_dlp: bool = False
    ffmpeg: bool = False
    imagemagick: bool = False
    wl_clipboard: bool = False
    grim: bool = False
    slurp: bool = False
    wf_recorder: bool = False
    swww: bool = False
    hyprctl: bool = False
    mako: bool = False
    waybar: bool = False
    rofi: bool = False
    dunst: bool = False
    nmcli: bool = False
    bluetoothctl: bool = False
    brightnessctl: bool = False
    pactl: bool = False
    playerctl: bool = False
    gcalcli: bool = False
    trash_cli: bool = False
    fdupes: bool = False
    rsync: bool = False
    transmission_cli: bool = False
    wget: bool = False
    curl: bool = False
    ollama_models: list = field(default_factory=list)


@dataclass
class AIInfo:
    ollama_running: bool = False
    available_models: list = field(default_factory=list)
    default_model: str = ""
    has_gemini: bool = False
    has_chromadb: bool = False
    vector_db_path: str = ""


@dataclass
class ConfigInfo:
    hyprland_conf: str = ""
    kitty_conf: str = ""
    zshrc: str = ""
    bashrc: str = ""
    nvim_conf: str = ""
    waybar_conf: str = ""
    mako_conf: str = ""
    spidy_conf: str = ""


@dataclass
class SystemProfile:
    collected_at: str = ""
    hardware: HardwareInfo = field(default_factory=HardwareInfo)
    os: OSInfo = field(default_factory=OSInfo)
    tools: ToolInfo = field(default_factory=ToolInfo)
    ai: AIInfo = field(default_factory=AIInfo)
    configs: ConfigInfo = field(default_factory=ConfigInfo)
    env: dict = field(default_factory=dict)


def _which(name: str) -> bool:
    return shutil.which(name) is not None


def _read_sysfs(path: str) -> str:
    p = Path(path)
    return p.read_text().strip() if p.exists() else ""


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def collect_profile() -> SystemProfile:
    """Collect a full system profile. Results are cached for reuse."""
    profile = SystemProfile(collected_at=datetime.now().isoformat())

    # ── Hardware ──────────────────────────────────────────────────────────
    cpu_info = _read_sysfs("/proc/cpuinfo")
    model_names = re.findall(r"model name\s+:\s+(.+)", cpu_info)
    profile.hardware.cpu = model_names[0] if model_names else ""
    profile.hardware.cores = len(re.findall(r"^processor\s+:", cpu_info, re.M))
    profile.hardware.threads = profile.hardware.cores

    mem_total = _read_sysfs("/proc/meminfo")
    m = re.search(r"MemTotal:\s+(\d+)", mem_total)
    if m:
        profile.hardware.ram_gb = round(int(m.group(1)) / 1_048_576, 1)

    gpu = _run(["lspci", "|", "grep", "-i", "vga"], timeout=5)
    if gpu:
        profile.hardware.gpu = gpu.split(":")[-1].strip() if ":" in gpu else gpu
    if not profile.hardware.gpu:
        profile.hardware.gpu = _run(["lspci"], timeout=5).split("\n")[0] or ""

    disk = _run(["df", "-h", "--output=size,used", "/"], timeout=5)
    lines = disk.splitlines()
    if len(lines) > 1:
        parts = lines[1].split()
        if len(parts) >= 2:
            size = parts[0].replace("G", "").replace("T", "")
            used = parts[1].replace("G", "").replace("T", "")
            try:
                profile.hardware.disk_total_gb = float(size)
                profile.hardware.disk_used_gb = float(used)
            except ValueError:
                pass

    # ── OS ────────────────────────────────────────────────────────────────
    profile.os.distro = _run(["lsb_release", "-sd"], timeout=3) or "Arch Linux"
    profile.os.kernel = _run(["uname", "-r"])
    profile.os.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Hyprland")
    profile.os.display_server = os.environ.get("XDG_SESSION_TYPE", "wayland")
    profile.os.shell = os.environ.get("SHELL", "zsh")
    profile.os.terminal = os.environ.get("TERMINAL", "kitty")

    # ── Tools ─────────────────────────────────────────────────────────────
    t = profile.tools
    t.ollama = _which("ollama")
    t.git = _which("git")
    t.python = _run(["python3", "--version"])
    t.node = _run(["node", "--version"])
    t.docker = _which("docker")
    t.yay = _which("yay")
    t.paru = _which("paru")
    t.neovim = _which("nvim")
    t.htop = _which("htop")
    t.btop = _which("btop")
    t.lazygit = _which("lazygit")
    t.tmux = _which("tmux")
    t.zoxide = _which("zoxide")
    t.fzf = _which("fzf")
    t.fd = _which("fd")
    t.ripgrep = _which("rg")
    t.eza = _which("eza")
    t.bat = _which("bat")
    t.jq = _which("jq")
    t.yt_dlp = _which("yt-dlp")
    t.ffmpeg = _which("ffmpeg")
    t.imagemagick = _which("magick") or _which("convert")
    t.wl_clipboard = _which("wl-copy")
    t.grim = _which("grim")
    t.slurp = _which("slurp")
    t.wf_recorder = _which("wf-recorder")
    t.swww = _which("swww")
    t.hyprctl = _which("hyprctl")
    t.mako = _which("mako")
    t.waybar = _which("waybar")
    t.rofi = _which("rofi")
    t.nmcli = _which("nmcli")
    t.bluetoothctl = _which("bluetoothctl")
    t.brightnessctl = _which("brightnessctl")
    t.pactl = _which("pactl")
    t.playerctl = _which("playerctl")
    t.trash_cli = _which("trash")
    t.fdupes = _which("fdupes")
    t.rsync = _which("rsync")
    t.transmission_cli = _which("transmission-remote")
    t.wget = _which("wget")
    t.curl = _which("curl")

    # ── AI / Ollama ───────────────────────────────────────────────────────
    if t.ollama:
        ai_list = _run(["ollama", "list"], timeout=10)
        if ai_list:
            t.ollama_models = [l.split()[0] for l in ai_list.splitlines()[1:] if l.strip()]
    profile.ai.ollama_running = bool(t.ollama_models)
    profile.ai.available_models = t.ollama_models
    profile.ai.default_model = t.ollama_models[0] if t.ollama_models else ""
    profile.ai.has_chromadb = _which("chromadb") or Path.cwd().joinpath("venv").exists()
    profile.ai.vector_db_path = str(Path.home() / ".cache" / "spidy" / "chroma")

    # ── Configs ───────────────────────────────────────────────────────────
    home = Path.home()
    for attr, path in [
        ("hyprland_conf", home / ".config/hypr/hyprland.conf"),
        ("kitty_conf", home / ".config/kitty/kitty.conf"),
        ("zshrc", home / ".zshrc"),
        ("bashrc", home / ".bashrc"),
        ("nvim_conf", home / ".config/nvim/init.lua"),
        ("waybar_conf", home / ".config/waybar/config.jsonc"),
        ("mako_conf", home / ".config/mako/config"),
        ("spidy_conf", Path.cwd() / "config.yaml"),
    ]:
        if path.exists():
            try:
                setattr(profile.configs, attr, path.read_text(encoding="utf-8", errors="ignore")[:2000])
            except Exception:
                pass

    # ── Env ───────────────────────────────────────────────────────────────
    for key in ["HYPRLAND_INSTANCE_SIGNATURE", "XDG_CURRENT_DESKTOP",
                 "XDG_SESSION_TYPE", "WAYLAND_DISPLAY", "TERM",
                 "EDITOR", "BROWSER", "FILE_MANAGER"]:
        val = os.environ.get(key, "")
        if val:
            profile.env[key] = val

    return profile


def profile_summary(profile: SystemProfile | None = None) -> str:
    """Return a concise text summary for the system prompt."""
    if profile is None:
        profile = collect_profile()
    h = profile.hardware
    o = profile.os
    t = profile.tools
    a = profile.ai

    lines = [
        f"System: {o.distro} | Kernel {o.kernel}",
        f"Desktop: {o.desktop} ({o.display_server}) | Shell: {o.shell} | Terminal: {o.terminal}",
        f"CPU: {h.cpu} ({h.cores}c/{h.threads}t) | RAM: {h.ram_gb} GB | GPU: {h.gpu}",
        f"Disk: {h.disk_used_gb}/{h.disk_total_gb} GB used",
        f"Ollama: {'running' if a.ollama_running else 'stopped'} | Models: {', '.join(a.available_models[:5]) or 'none'}",
        f"Tools: yay={t.yay} git={t.git} nvim={t.neovim} htop={t.htop} fzf={t.fzf}",
    ]
    return "\n".join(lines)


# ── Cache ─────────────────────────────────────────────────────────────────────
_profile_cache: SystemProfile | None = None

def get_profile(force: bool = False) -> SystemProfile:
    global _profile_cache
    if _profile_cache is None or force:
        _profile_cache = collect_profile()
    return _profile_cache
