import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_BACKUP_SCRIPT = Path.home() / "abix_scripts" / "backup_dotfiles.sh"
_ALT_SCRIPT = Path.home() / "abix_backup.sh"

class DotfilesSkill(BaseSkill):
    name = "dotfiles"
    description = "Backup dotfiles using the configured backup script"
    triggers = ["backup dotfiles", "dotfiles", "backup config", "save dotfiles", "dot backup"]

    def run(self, text: str, lang: str = "en") -> dict:
        script = None
        if _BACKUP_SCRIPT.exists():
            script = _BACKUP_SCRIPT
        elif _ALT_SCRIPT.exists():
            script = _ALT_SCRIPT
        if script:
            try:
                subprocess.run([str(script)], check=True, timeout=120)
                return {"success": True, "speak_en": "Dotfiles backed up.", "speak_ta": "Dotfiles backup பண்ணேன் அண்ணா."}
            except subprocess.TimeoutExpired:
                return {"success": False, "speak_en": "Backup timed out.", "speak_ta": "Backup timeout அண்ணா."}
            except subprocess.CalledProcessError as e:
                return {"success": False, "speak_en": f"Backup failed: {e}", "speak_ta": "Backup fail அண்ணா."}
        git_dir = Path.home() / "dotfiles"
        if git_dir.exists() and (git_dir / ".git").exists():
            try:
                subprocess.run(["git", "add", "-A"], cwd=git_dir, check=True, timeout=10)
                subprocess.run(["git", "commit", "-m", "auto backup"], cwd=git_dir, check=False, timeout=10)
                subprocess.run(["git", "push"], cwd=git_dir, check=False, timeout=30)
                return {"success": True, "speak_en": "Dotfiles backed up to git.", "speak_ta": "Dotfiles backup பண்ணேன் அண்ணா."}
            except Exception as e:
                return {"success": False, "speak_en": f"Git backup failed: {e}", "speak_ta": "Git backup fail அண்ணா."}
        return {"success": False, "speak_en": "No backup script or dotfiles git repo found.", "speak_ta": "Backup script இல்ல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("backup dotfiles")["speak_en"])
