from skills.schedule.set_reminder import SetReminderSkill
from skills.schedule.list_reminders import ListRemindersSkill
from skills.schedule.delete_reminder import DeleteReminderSkill
from skills.schedule.recurring_alarm import RecurringAlarmSkill
from skills.schedule.add_todo import AddTodoSkill
from skills.schedule.list_todos import ListTodosSkill
from skills.schedule.mark_todo import MarkTodoSkill
from skills.schedule.daily_briefing import DailyBriefingSkill
from skills.schedule.pomodoro import PomodoroSkill
from skills.schedule.study_tracker import StudyTrackerSkill
from skills.schedule.deadline_alert import DeadlineAlertSkill
from skills.schedule.calendar_sync import CalendarSyncSkill
from skills.schedule.quick_note import QuickNoteSkill
from skills.schedule.note_search import NoteSearchSkill
from skills.schedule.weekly_summary import WeeklySummarySkill

SCHEDULE_SKILLS: list = [
    SetReminderSkill, ListRemindersSkill, DeleteReminderSkill,
    RecurringAlarmSkill, AddTodoSkill, ListTodosSkill, MarkTodoSkill,
    DailyBriefingSkill, PomodoroSkill, StudyTrackerSkill, DeadlineAlertSkill,
    CalendarSyncSkill, QuickNoteSkill, NoteSearchSkill, WeeklySummarySkill,
]

__all__ = ["SCHEDULE_SKILLS"] + [s.__name__ for s in SCHEDULE_SKILLS]
