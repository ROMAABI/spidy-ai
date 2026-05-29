from skills.files.find_file import FindFileSkill
from skills.files.grep_file import GrepFileSkill
from skills.files.open_file import OpenFileSkill
from skills.files.move_copy_delete import MoveCopyDeleteSkill
from skills.files.rename import RenameSkill
from skills.files.create_folder import CreateFolderSkill
from skills.files.archive import ArchiveSkill
from skills.files.duplicates import DuplicatesSkill
from skills.files.large_files import LargeFilesSkill
from skills.files.old_files import OldFilesSkill
from skills.files.download_url import DownloadUrlSkill
from skills.files.monitor_downloads import MonitorDownloadsSkill
from skills.files.auto_sort import AutoSortSkill
from skills.files.torrent import TorrentSkill
from skills.files.yt_dlp import YtDlpSkill
from skills.files.anime_rename import AnimeRenameSkill
from skills.files.dotfiles import DotfilesSkill
from skills.files.sync_external import SyncExternalSkill
from skills.files.disk_usage import DiskUsageSkill
from skills.files.trash import TrashSkill

FILES_SKILLS: list = [
    FindFileSkill, GrepFileSkill, OpenFileSkill, MoveCopyDeleteSkill,
    RenameSkill, CreateFolderSkill, ArchiveSkill, DuplicatesSkill,
    LargeFilesSkill, OldFilesSkill, DownloadUrlSkill, MonitorDownloadsSkill,
    AutoSortSkill, TorrentSkill, YtDlpSkill, AnimeRenameSkill,
    DotfilesSkill, SyncExternalSkill, DiskUsageSkill, TrashSkill,
]

__all__ = ["FILES_SKILLS"] + [s.__name__ for s in FILES_SKILLS]
