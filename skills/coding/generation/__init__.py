from skills.coding.generation.generate_function import GenerateFunctionSkill
from skills.coding.generation.generate_boilerplate import GenerateBoilerplateSkill
from skills.coding.generation.generate_tests import GenerateTestsSkill
from skills.coding.generation.generate_type_hints import GenerateTypeHintsSkill
from skills.coding.generation.generate_docstrings import GenerateDocstringsSkill

GENERATION_SKILLS = [
    GenerateFunctionSkill, GenerateBoilerplateSkill, GenerateTestsSkill,
    GenerateTypeHintsSkill, GenerateDocstringsSkill,
]
