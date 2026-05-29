from skills.coding.understanding.read_and_summarize import ReadAndSummarizeSkill
from skills.coding.understanding.explain_function import ExplainFunctionSkill
from skills.coding.understanding.trace_execution import TraceExecutionSkill
from skills.coding.understanding.detect_code_smells import DetectCodeSmellsSkill
from skills.coding.understanding.explain_project_structure import ExplainProjectStructureSkill
from skills.coding.understanding.parse_error import ParseErrorSkill
from skills.coding.understanding.find_dead_code import FindDeadCodeSkill
from skills.coding.understanding.explain_regex import ExplainRegexSkill
from skills.coding.understanding.explain_sql import ExplainSqlSkill
from skills.coding.understanding.explain_config import ExplainConfigSkill

UNDERSTANDING_SKILLS = [
    ReadAndSummarizeSkill, ExplainFunctionSkill, TraceExecutionSkill,
    DetectCodeSmellsSkill, ExplainProjectStructureSkill, ParseErrorSkill,
    FindDeadCodeSkill, ExplainRegexSkill, ExplainSqlSkill, ExplainConfigSkill,
]
