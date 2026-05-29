"""
spidy/commands/profile.py
"""

from spidy.profile import get_profile, profile_summary
import json


class ProfileCommand:
    """spidy profile — Display system profile."""

    @staticmethod
    def show() -> str:
        profile = get_profile(force=True)
        return profile_summary(profile)

    @staticmethod
    def json_output() -> str:
        from dataclasses import asdict
        profile = get_profile(force=True)
        return json.dumps(asdict(profile), indent=2, default=str)

    @staticmethod
    def tools() -> str:
        profile = get_profile()
        t = profile.tools
        available = []
        for attr in dir(t):
            if not attr.startswith("_") and not callable(getattr(t, attr)):
                val = getattr(t, attr)
                if isinstance(val, bool) and val:
                    available.append(attr)
                elif isinstance(val, str) and val:
                    available.append(f"{attr}={val}")
        return "Installed tools:\n" + "\n".join(f"  ✓ {a}" for a in sorted(available))
