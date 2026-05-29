"""
Dynamic theme detection for Spidy AI TUI.

Detects system colors from multiple Linux desktop sources (Pywal, GTK,
Hyprland, HyDE, Waybar) and maps them to Textual Theme tokens with
contrast-safe fallbacks and live reload support.
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")
_HEX_SHORT_RE = re.compile(r"^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$")


def _parse_hex(hex_str: str) -> tuple[int, int, int] | None:
    """Parse a hex color string to (r, g, b) 0-255."""
    m = _HEX_RE.match(hex_str)
    if m:
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
    m = _HEX_SHORT_RE.match(hex_str)
    if m:
        return (int(m.group(1) * 2, 16), int(m.group(2) * 2, 16), int(m.group(3) * 2, 16))
    return None


def _to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance."""
    def channel(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1 = _relative_luminance(*a)
    l2 = _relative_luminance(*b)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _best_text_color(
    bg: tuple[int, int, int],
    light_text: tuple[int, int, int] = (229, 229, 229),
    dark_text: tuple[int, int, int] = (30, 30, 30),
) -> str:
    """Return the hex string (light or dark) that gives the best contrast on *bg*."""
    light_ratio = _contrast_ratio(bg, light_text)
    dark_ratio = _contrast_ratio(bg, dark_text)
    return _to_hex(*light_text) if light_ratio >= dark_ratio else _to_hex(*dark_text)


def _blend(over: tuple[int, int, int], alpha: float) -> str:
    """Blend a color toward white by *alpha* (0-1). Lighter variant."""
    r = min(255, int(over[0] + (255 - over[0]) * alpha))
    g = min(255, int(over[1] + (255 - over[1]) * alpha))
    b = min(255, int(over[2] + (255 - over[2]) * alpha))
    return _to_hex(r, g, b)


def _blend_dark(over: tuple[int, int, int], alpha: float) -> str:
    """Blend a color toward black by *alpha* (0-1). Darker variant."""
    r = max(0, int(over[0] - over[0] * alpha))
    g = max(0, int(over[1] - over[1] * alpha))
    b = max(0, int(over[2] - over[2] * alpha))
    return _to_hex(r, g, b)


# ---------------------------------------------------------------------------
# Theme color data
# ---------------------------------------------------------------------------

@dataclass
class SpidyThemeColors:
    """Normalised color tokens for Spidy."""

    # Core
    primary: str = "#2d0710"          # accent / user message bg (dark red)
    accent: str = "#00f0ff"           # lighter accent / borders / highlights (cyan)
    foreground: str = "#e5e5e5"       # main text
    background: str = "#120204"       # root background (very dark red-black)
    surface: str = "#23050b"          # cards / inputs / sidebar (dark red)
    panel: str = "#2d0710"            # dialog backgrounds

    # Semantic
    success: str = "#10b981"
    error: str = "#ef4444"
    warning: str = "#f59e0b"

    # Custom extras (passed via Theme.variables)
    text_dim: str = "#737373"
    selection_bg: str = "#00f0ff"
    scrollbar_bg: str = "#23050b"
    scrollbar_active: str = "#00f0ff"
    border_focus: str = "#00f0ff"

    @classmethod
    def default_dark(cls) -> SpidyThemeColors:
        """Professional dark fallback if no theme source is found."""
        return cls()

    def to_textual_theme_variables(self) -> dict[str, str]:
        """Extra CSS custom properties beyond standard Textual Theme fields."""
        return {
            "--spidy-text-dim": self.text_dim,
            "--spidy-selection-bg": self.selection_bg,
            "--spidy-scrollbar-bg": self.scrollbar_bg,
            "--spidy-scrollbar-active": self.scrollbar_active,
            "--spidy-border-focus": self.border_focus,
        }


# ---------------------------------------------------------------------------
# Source detectors
# ---------------------------------------------------------------------------

def _detect_pywal() -> dict[str, str] | None:
    """Read colours from ~/.cache/wal/colors.json (pywal)."""
    path = Path.home() / ".cache" / "wal" / "colors.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        raw = data.get("colors", {})
        special = data.get("special", {})
        # Pywal gives 16 colours (color0..color15) plus special keys
        colors: dict[str, str] = {}
        for k, v in raw.items():
            if isinstance(v, str) and v.startswith("#") and len(v) in (4, 7):
                colors[k] = v
        if special.get("background"):
            colors["background"] = special["background"]
        if special.get("foreground"):
            colors["foreground"] = special["foreground"]
        if special.get("cursor"):
            colors["cursor"] = special["cursor"]
        return colors
    except Exception:
        return None


def _detect_gtk() -> dict[str, str] | None:
    """Read GTK theme name from settings.ini and try to extract colours."""
    for ini_path in [
        Path.home() / ".config" / "gtk-3.0" / "settings.ini",
        Path.home() / ".config" / "gtk-4.0" / "settings.ini",
    ]:
        if not ini_path.exists():
            continue
        try:
            text = ini_path.read_text()
            # Extract theme name
            m = re.search(r"gtk-theme-name\s*=\s*([^\n\r]+)", text)
            if not m:
                continue
            theme_name = m.group(1).strip().strip('"').strip("'")

            # Try common GTK CSS file locations
            search_dirs = [
                Path.home() / ".themes" / theme_name,
                Path.home() / ".local" / "share" / "themes" / theme_name,
                Path(f"/usr/share/themes/{theme_name}"),
            ]
            for theme_dir in search_dirs:
                if not theme_dir.exists():
                    continue
                for css_file in theme_dir.rglob("*.css"):
                    if css_file.stat().st_size > 100_000:
                        continue  # skip huge bundles
                    content = css_file.read_text()
                    colors = _extract_css_colors(content)
                    if colors:
                        return colors
        except Exception:
            continue
    return None


def _detect_hyprland() -> dict[str, str] | None:
    """Read colour variables from hyprland.conf."""
    conf_path = Path.home() / ".config" / "hypr" / "hyprland.conf"
    if not conf_path.exists():
        return None
    try:
        colors: dict[str, str] = {}
        for line in conf_path.read_text().splitlines():
            line = line.strip()
            # Hyprland variable: $name = value
            if line.startswith("$") and "=" in line:
                parts = line[1:].split("=", 1)
                key = parts[0].strip().lower()
                val = parts[1].strip().strip("'\"")
                if val.startswith("rgb("):
                    # rgb(r,g,b) → #rrggbb
                    m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", val)
                    if m:
                        colors[key] = _to_hex(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                elif val.startswith("#"):
                    colors[key] = val
        return colors if colors else None
    except Exception:
        return None


def _detect_hyde() -> dict[str, str] | None:
    """Read colours from HyDE config directory (~/.config/hyde/)."""
    hyde_dir = Path.home() / ".config" / "hyde"
    if not hyde_dir.exists():
        return None
    try:
        colors: dict[str, str] = {}
        # HyDE stores theme in various files
        for pattern in ["*.theme", "*.conf", "*.json"]:
            for f in hyde_dir.glob(pattern):
                if f.stat().st_size > 50_000:
                    continue
                text = f.read_text()
                # Try JSON
                if f.suffix == ".json":
                    try:
                        data = json.loads(text)
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, str) and v.startswith("#"):
                                    colors[k.lower()] = v
                    except Exception:
                        pass
                # Try KEY=VALUE or CSS-style
                for line in text.splitlines():
                    line = line.strip()
                    for m in re.finditer(r"(#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))", line):
                        colors.setdefault(f"hyde_color_{len(colors)}", m.group(1))
        return colors if colors else None
    except Exception:
        return None


def _detect_waybar() -> dict[str, str] | None:
    """Read colour values from waybar style.css."""
    css_path = Path.home() / ".config" / "waybar" / "style.css"
    if not css_path.exists():
        return None
    try:
        colors = _extract_css_colors(css_path.read_text())
        return colors if colors else None
    except Exception:
        return None


_CSS_COLOR_RE = re.compile(
    r"(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})"
)


def _extract_css_colors(css: str) -> dict[str, str]:
    """Extract hex colour values from CSS text with key names if available."""
    colors: dict[str, str] = {}
    # Try to match CSS custom properties like --color-name: #xxx
    for line in css.splitlines():
        line = line.strip()
        m = re.match(r"--([a-zA-Z][\w-]*)\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b", line)
        if m:
            colors[m.group(1).lower()] = m.group(2)
    # Also grab @define-color for GTK CSS
    for line in css.splitlines():
        line = line.strip()
        m = re.match(r"@define-color\s+(\S+)\s+(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b", line)
        if m:
            colors[m.group(1).lower()] = m.group(2)
    # Collect all hex codes as fallback
    if not colors:
        hexes = _CSS_COLOR_RE.findall(css)
        for i, h in enumerate(hexes):
            colors[f"css_color_{i}"] = h
    return colors


# ---------------------------------------------------------------------------
# Source priority
# ---------------------------------------------------------------------------

_SOURCES: list[tuple[str, Callable[[], dict[str, str] | None]]] = [
    ("pywal", _detect_pywal),
    ("hyprland", _detect_hyprland),
    ("hyde", _detect_hyde),
    ("waybar", _detect_waybar),
    ("gtk", _detect_gtk),
]


# ---------------------------------------------------------------------------
# Mapping from source colours → Spidy tokens
# ---------------------------------------------------------------------------

def _map_pywal(colors: dict[str, str]) -> SpidyThemeColors:
    """Map pywal colour dict to SpidyThemeColors."""
    bg = _parse_hex(colors.get("background", "") or "#1e1e1e") or (30, 30, 30)
    fg = _parse_hex(colors.get("foreground", "") or "#e5e5e5") or (229, 229, 229)
    c0 = _parse_hex(colors.get("color0", "")) or bg
    c1 = _parse_hex(colors.get("color1", "")) or (91, 33, 182)
    c2 = _parse_hex(colors.get("color2", "")) or (16, 185, 129)
    c3 = _parse_hex(colors.get("color3", "")) or (245, 158, 11)
    c4 = _parse_hex(colors.get("color4", "")) or (124, 58, 237)
    c5 = _parse_hex(colors.get("color5", "")) or (239, 68, 68)
    c6 = _parse_hex(colors.get("color6", "")) or (20, 184, 166)
    c7 = _parse_hex(colors.get("color7", "")) or fg

    primary_hex = _to_hex(*c4)
    accent_hex = _blend(c4, 0.15)
    surface_hex = _blend(c0, 0.08)

    bg_hex = _to_hex(*bg)
    fg_hex = _to_hex(*fg)

    return SpidyThemeColors(
        primary=primary_hex,
        accent=accent_hex,
        foreground=_best_text_color(bg, fg, (30, 30, 30)) if bg == c0 else fg_hex,
        background=bg_hex,
        surface=surface_hex,
        panel=_blend(c0, 0.15),
        success=_to_hex(*c2),
        error=_to_hex(*c5),
        warning=_to_hex(*c3),
        text_dim=_blend(fg if fg != bg else (200, 200, 200), 0.45),
        selection_bg=accent_hex,
        scrollbar_bg=surface_hex,
        scrollbar_active=primary_hex,
        border_focus=accent_hex,
    )


def _map_generic(colors: dict[str, str]) -> SpidyThemeColors:
    """Generic mapping for non-pywal sources — tries to pick primary/secondary."""
    hexes = [v for v in colors.values() if v.startswith("#") and len(v) in (4, 7)]
    if not hexes:
        return SpidyThemeColors.default_dark()

    parsed = [p for p in (_parse_hex(h) for h in hexes) if p is not None]
    if not parsed:
        return SpidyThemeColors.default_dark()

    # Sort by luminance — darkest first
    parsed.sort(key=lambda c: _relative_luminance(*c))
    darkest = parsed[0]
    lightest = parsed[-1]

    dark_lum = _relative_luminance(*darkest)

    # If nothing is truly dark, the source isn't a dark theme — return fallback
    if dark_lum > 0.1:
        return SpidyThemeColors.default_dark()
    else:
        bg = darkest
        fg = lightest
        # Pick mid-luminance colors for primary/accent (skip darkest and lightest)
        candidates = parsed[1:-1] if len(parsed) > 2 else parsed
        primary = candidates[len(candidates) // 2] if candidates else (91, 33, 182)
        accent = _parse_hex(_blend(primary, 0.2)) or primary

    surface = _parse_hex(_blend(bg, 0.08)) or bg
    panel = _parse_hex(_blend(bg, 0.18)) or (51, 51, 51)
    fg_hex = _to_hex(*fg)
    dim = _parse_hex(_blend(fg, 0.50)) or (136, 136, 136)

    return SpidyThemeColors(
        primary=_to_hex(*primary),
        accent=_to_hex(*accent),
        foreground=_best_text_color(bg, fg, (30, 30, 30)),
        background=_to_hex(*bg),
        surface=_to_hex(*surface),
        panel=_to_hex(*panel),
        text_dim=_to_hex(*dim),
        selection_bg=_to_hex(*accent),
        scrollbar_bg=_to_hex(*surface),
        scrollbar_active=_to_hex(*primary),
        border_focus=_to_hex(*accent),
    )


# ---------------------------------------------------------------------------
# ThemeManager
# ---------------------------------------------------------------------------

@dataclass
class ThemeManager:
    """Detects, caches, and delivers theme colours for Spidy TUI.

    Usage::

        mgr = ThemeManager()
        mgr.detect()
        theme = mgr.theme  # SpidyThemeColors instance
        mgr.on_change(lambda t: app.apply_theme(t))
        await mgr.start_watching()

    Call :meth:`detect` before reading :attr:`theme`.
    """

    cache_path: Path = field(default_factory=lambda: Path.home() / ".cache" / "spidy" / "theme_cache.json")
    active_source: str = "fallback"
    theme: SpidyThemeColors = field(default_factory=SpidyThemeColors.default_dark)
    _listeners: list[Callable[[SpidyThemeColors], None]] = field(default_factory=list)
    _watched_paths: list[Path] = field(default_factory=list)

    # ── Detection ─────────────────────────────────────────────────────

    def detect(self, force: bool = False) -> SpidyThemeColors:
        """Run all source detectors in priority order and return the result.

        Caches the result to ``~/.cache/spidy/theme_cache.json`` so that
        subsequent launches are fast even without detection.
        """
        if not force:
            cached = self._load_cache()
            if cached is not None:
                self.theme = cached
                return cached

        for source_name, detector in _SOURCES:
            raw = detector()
            if raw:
                self.active_source = source_name
                self._watched_paths = list(self._detect_watch_paths(source_name))
                if source_name == "pywal":
                    self.theme = _map_pywal(raw)
                else:
                    self.theme = _map_generic(raw)
                self._ensure_contrast()
                self._save_cache(self.theme)
                return self.theme

        self.active_source = "fallback"
        self.theme = SpidyThemeColors.default_dark()
        self._save_cache(self.theme)
        return self.theme

    # ── Contrast enforcement ──────────────────────────────────────────

    def _ensure_contrast(self) -> None:
        """Ensure all text-on-background combinations meet WCAG AA (4.5:1)."""
        bg = _parse_hex(self.theme.background) or (30, 30, 30)
        surface = _parse_hex(self.theme.surface) or (42, 42, 42)
        panel = _parse_hex(self.theme.panel) or (51, 51, 51)

        # Foreground on background
        self.theme.foreground = _best_text_color(bg)
        # Text-dim on background (ensure ≥ 3:1 for large text)
        dim = _parse_hex(self.theme.text_dim) or (136, 136, 136)
        if _contrast_ratio(dim, bg) < 3.0:
            self.theme.text_dim = _to_hex(*dim) if _contrast_ratio(dim, bg) >= 3.0 else _best_text_color(bg)

        # Text on surface (sidebar, inputs)
        fg_on_surface = _best_text_color(surface)
        self.theme.foreground = fg_on_surface  # overrides for surface context
        # Primary on surface (user message bubbles)
        primary_rgb = _parse_hex(self.theme.primary) or (91, 33, 182)
        self.theme.primary = _to_hex(*primary_rgb)
        # Text on primary (user message text)
        user_text = _best_text_color(primary_rgb)
        # We store the user-message text colour as an extra variable
        self._user_text_on_primary = user_text

    # ── File watching ─────────────────────────────────────────────────

    def _detect_watch_paths(self, source: str) -> list[Path]:
        paths: list[Path] = []
        home = Path.home()
        if source == "pywal":
            cache = home / ".cache" / "wal"
            if cache.exists():
                paths.append(cache / "colors.json")
        elif source == "hyprland":
            cfg = home / ".config" / "hypr"
            if cfg.exists():
                paths.append(cfg / "hyprland.conf")
        elif source == "hyde":
            cfg = home / ".config" / "hyde"
            if cfg.exists():
                paths.extend(cfg.iterdir())
        elif source == "waybar":
            cfg = home / ".config" / "waybar"
            if cfg.exists():
                paths.append(cfg / "style.css")
        elif source == "gtk":
            for p in [home / ".config" / "gtk-3.0" / "settings.ini",
                       home / ".config" / "gtk-4.0" / "settings.ini"]:
                if p.exists():
                    paths.append(p)
        return paths

    def on_change(self, cb: Callable[[SpidyThemeColors], None]) -> None:
        """Register a callback invoked when the theme reloads."""
        self._listeners.append(cb)

    async def start_watching(self) -> None:
        """Watch theme source files for changes and call listeners on change.

        Uses ``watchfiles`` (installed separately) or falls back to a simple
        polling loop.
        """
        if not self._watched_paths:
            return

        try:
            import watchfiles  # noqa: F401
            await self._watch_watchfiles()
        except ImportError:
            await self._watch_polling()

    async def _watch_watchfiles(self) -> None:
        import watchfiles

        paths = [str(p) for p in self._watched_paths if p.exists()]

        async for _ in watchfiles.awatch(*paths):
            # Debounce: wait for file to finish writing
            import asyncio
            await asyncio.sleep(0.3)
            self.detect(force=True)
            for cb in self._listeners:
                cb(self.theme)

    async def _watch_polling(self) -> None:
        """Poll-based fallback watcher."""
        import asyncio
        from datetime import datetime, timezone

        mtimes = {p: (p.stat().st_mtime if p.exists() else 0) for p in self._watched_paths}

        while True:
            await asyncio.sleep(2.0)
            changed = False
            for p in self._watched_paths:
                current = p.stat().st_mtime if p.exists() else 0
                if current != mtimes.get(p, 0):
                    mtimes[p] = current
                    changed = True
            if changed:
                self.detect(force=True)
                for cb in self._listeners:
                    cb(self.theme)

    # ── Cache ─────────────────────────────────────────────────────────

    def _load_cache(self) -> SpidyThemeColors | None:
        try:
            if self.cache_path.exists():
                data = json.loads(self.cache_path.read_text())
                return SpidyThemeColors(**data)
        except Exception:
            pass
        return None

    def _save_cache(self, theme: SpidyThemeColors) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(theme.__dict__, indent=2)
            )
        except Exception:
            pass
