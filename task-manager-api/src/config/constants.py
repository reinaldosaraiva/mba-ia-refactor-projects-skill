from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


VALID_STATUSES = [s.value for s in TaskStatus]
VALID_ROLES = [r.value for r in UserRole]
TERMINAL_STATUSES = frozenset({TaskStatus.DONE.value, TaskStatus.CANCELLED.value})

TASK_TITLE_MIN_LEN = 3
TASK_TITLE_MAX_LEN = 200
TASK_PRIORITY_MIN = 1
TASK_PRIORITY_MAX = 5
TASK_DEFAULT_PRIORITY = 3

USER_PASSWORD_MIN_LEN = 4

CATEGORY_DEFAULT_COLOR = "#000000"

RECENT_ACTIVITY_DAYS = 7
