"""
spidy/config.py — Configuration loader.

Loads config.yaml and provides typed access to all settings.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BrainConfig:
    system_prompt: str = ""
    temperature: float = 0.3
    cloud_model: str = ""
    local_model: str = ""
    context_length: int = 4096


@dataclass
class MemoryConfig:
    sqlite_path: str = ""
    chroma_path: str = ""
    max_history: int = 50


@dataclass
class SttConfig:
    model: str = "base"
    language: str = "en"
    energy_threshold: int = 300


@dataclass
class TtsConfig:
    enabled: bool = True
    voice: str = "default"


@dataclass
class SpidyConfig:
    brain: BrainConfig = field(default_factory=BrainConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    profile_auto_refresh: bool = True
    knowledge_dirs: list = field(default_factory=list)
    debug: bool = False
    raw: dict = field(default_factory=dict)


_CONFIG_CACHE: SpidyConfig | None = None


def load_config(path: str | None = None) -> SpidyConfig:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and path is None:
        return _CONFIG_CACHE

    cfg_path = Path(path or "config.yaml")
    if not cfg_path.exists():
        cfg_path = Path.cwd() / "config.yaml"
    if not cfg_path.exists():
        cfg_path = Path.home() / ".config/spidy/config.yaml"

    raw = {}
    if cfg_path.exists():
        with open(cfg_path) as f:
            raw = yaml.safe_load(f) or {}

    brain_raw = raw.get("brain", {})
    mem_raw = raw.get("memory", {})
    stt_raw = raw.get("stt", {})
    tts_raw = raw.get("tts", {})

    config = SpidyConfig(
        brain=BrainConfig(
            system_prompt=brain_raw.get("system_prompt", ""),
            temperature=brain_raw.get("temperature", 0.3),
            cloud_model=brain_raw.get("cloud_model", ""),
            local_model=brain_raw.get("local_model", ""),
            context_length=brain_raw.get("context_length", 4096),
        ),
        memory=MemoryConfig(
            sqlite_path=mem_raw.get("sqlite_path", "/tmp/spidy_memory.db"),
            chroma_path=mem_raw.get("chroma_path", str(Path.home() / ".cache/spidy/chroma")),
            max_history=mem_raw.get("max_history", 50),
        ),
        stt=SttConfig(
            model=stt_raw.get("model", "base"),
            language=stt_raw.get("language", "en"),
            energy_threshold=stt_raw.get("energy_threshold", 300),
        ),
        tts=TtsConfig(
            enabled=tts_raw.get("enabled", True),
            voice=tts_raw.get("voice", "default"),
        ),
        profile_auto_refresh=raw.get("profile_auto_refresh", True),
        knowledge_dirs=raw.get("knowledge_dirs", []),
        debug=raw.get("debug", False),
        raw=raw,
    )

    _CONFIG_CACHE = config
    return config


def get_config(force: bool = False) -> SpidyConfig:
    return load_config() if force or _CONFIG_CACHE is None else _CONFIG_CACHE
