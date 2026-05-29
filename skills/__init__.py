"""
skills — all skill categories.

Import helpers:

    from skills import ALL_SKILLS  # list of all skill classes
    from skills.system import SYSTEM_SKILLS
    from skills.schedule import SCHEDULE_SKILLS
    from skills.files import FILES_SKILLS
"""

from skills.system import SYSTEM_SKILLS
from skills.schedule import SCHEDULE_SKILLS
from skills.files import FILES_SKILLS
from skills.coding import CODING_SKILLS  # type: ignore[import-untyped]

ALL_SKILLS = SYSTEM_SKILLS + SCHEDULE_SKILLS + FILES_SKILLS + CODING_SKILLS

__all__ = [
    "SYSTEM_SKILLS", "SCHEDULE_SKILLS", "FILES_SKILLS",
    "CODING_SKILLS", "ALL_SKILLS",
]
