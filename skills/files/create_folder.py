from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class CreateFolderSkill(BaseSkill):
    name = "create_folder"
    description = "Create a folder / directory structure"
    triggers = ["create folder", "make directory", "new folder", "folder create", "mkdir"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["create folder", "make directory", "new folder", "folder create", "mkdir", "create"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "What folder name?", "speak_ta": "Folder name சொல்லுங்க அண்ணா?"}
        p = Path(t).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return {"success": True, "speak_en": f"Created folder: {p}", "speak_ta": f"Folder create பண்ணேன்: {p.name}"}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "path": {"type": "string", "description": "Folder path to create"},
        }, "required": ["path"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"create folder {kwargs.get('path', '')}")["speak_en"])
