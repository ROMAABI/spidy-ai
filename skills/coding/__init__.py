from skills.coding.understanding import UNDERSTANDING_SKILLS
from skills.coding.generation import GENERATION_SKILLS
from skills.coding.refactoring import REFACTORING_SKILLS
from skills.coding.debugging import DEBUGGING_SKILLS
from skills.coding.search import SEARCH_SKILLS

CODING_SKILLS = (
    UNDERSTANDING_SKILLS + GENERATION_SKILLS +
    REFACTORING_SKILLS + DEBUGGING_SKILLS + SEARCH_SKILLS
)

def get_all_tool_schemas() -> list[dict]:
    return [s.tool_schema() for s in CODING_SKILLS]

__all__ = ["CODING_SKILLS", "get_all_tool_schemas"]
