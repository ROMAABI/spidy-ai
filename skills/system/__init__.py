from skills.system.app_control import AppControlSkill
from skills.system.volume import VolumeSkill
from skills.system.brightness import BrightnessSkill
from skills.system.screenshot import ScreenshotSkill
from skills.system.screen_record import ScreenRecordSkill
from skills.system.wifi import WifiSkill
from skills.system.bluetooth import BluetoothSkill
from skills.system.battery import BatterySkill
from skills.system.display import DisplaySkill
from skills.system.workspace import WorkspaceSkill
from skills.system.wallpaper import WallpaperSkill
from skills.system.night_mode import NightModeSkill
from skills.system.do_not_disturb import DoNotDisturbSkill
from skills.system.process import ProcessSkill
from skills.system.system_stats import SystemStatsSkill

SYSTEM_SKILLS: list = [
    AppControlSkill, VolumeSkill, BrightnessSkill, ScreenshotSkill,
    ScreenRecordSkill, WifiSkill, BluetoothSkill, BatterySkill,
    DisplaySkill, WorkspaceSkill, WallpaperSkill, NightModeSkill,
    DoNotDisturbSkill, ProcessSkill, SystemStatsSkill,
]

__all__ = ["SYSTEM_SKILLS"] + [s.__name__ for s in SYSTEM_SKILLS]
