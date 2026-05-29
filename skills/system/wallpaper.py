import asyncio, subprocess, os, random
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

WALL_DIR = Path.home() / "Pictures" / "wallpapers"

class WallpaperSkill(BaseSkill):
    name = "wallpaper"
    description = "Change the desktop wallpaper"
    triggers = ["wallpaper", "wall", "background", "change wallpaper", "set wallpaper", "wal"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "hyde" in t or "wallbash" in t:
            subprocess.Popen(["hyde-wallpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": "Running HyDE wallpaper changer.", "speak_ta": "Wallpaper மாத்துறேன் அண்ணா."}
        if WALL_DIR.exists():
            images = list(WALL_DIR.glob("*.[pj][pn][g]")) + list(WALL_DIR.glob("*.jpg"))
            if images:
                img = random.choice(images)
                subprocess.Popen(["swww", "img", str(img)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"success": True, "speak_en": f"Wallpaper set to {img.name}.", "speak_ta": "Wallpaper மாத்தினேன் அண்ணா."}
        return {"success": False, "speak_en": "No wallpapers found.", "speak_ta": "Wallpaper கிடைக்கல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "source": {"type": "string", "enum": ["hyde", "random", "path"], "description": "Wallpaper source"},
            "path": {"type": "string", "description": "Path to a specific image"},
        }, "required": ["source"]}

    async def execute(self, **kwargs) -> SkillResult:
        path = kwargs.get("path", "")
        if path and Path(path).exists():
            subprocess.Popen(["swww", "img", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return SkillResult(success=True, output=f"Wallpaper set to {Path(path).name}.")
        return SkillResult(success=True, output=self.run("hyde")["speak_en"])
