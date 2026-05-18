from datetime import timedelta

from sqlalchemy import case, func

from src.config.constants import RECENT_ACTIVITY_DAYS, TERMINAL_STATUSES
from src.errors import NotFoundError
from src.models import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.helpers import now_utc


def build_summary():
    reference = now_utc()

    total_tasks = db.session.query(func.count(Task.id)).scalar() or 0
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_categories = db.session.query(func.count(Category.id)).scalar() or 0

    by_status = dict(
        db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    by_priority = dict(
        db.session.query(Task.priority, func.count(Task.id))
        .group_by(Task.priority)
        .all()
    )

    overdue_rows = (
        Task.query
        .filter(Task.due_date.isnot(None))
        .filter(Task.due_date < reference)
        .filter(~Task.status.in_(list(TERMINAL_STATUSES)))
        .all()
    )
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (reference - t.due_date).days,
        }
        for t in overdue_rows
    ]

    cutoff = reference - timedelta(days=RECENT_ACTIVITY_DAYS)
    recent_tasks = (
        db.session.query(func.count(Task.id))
        .filter(Task.created_at >= cutoff)
        .scalar()
        or 0
    )
    recent_done = (
        db.session.query(func.count(Task.id))
        .filter(Task.status == "done")
        .filter(Task.updated_at >= cutoff)
        .scalar()
        or 0
    )

    user_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .all()
    )
    user_stats = []
    for uid, uname, total, done in user_rows:
        total = total or 0
        done = int(done or 0)
        user_stats.append({
            "user_id": uid,
            "user_name": uname,
            "total_tasks": total,
            "completed_tasks": done,
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        })

    return {
        "generated_at": str(reference),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": by_status.get("pending", 0),
            "in_progress": by_status.get("in_progress", 0),
            "done": by_status.get("done", 0),
            "cancelled": by_status.get("cancelled", 0),
        },
        "tasks_by_priority": {
            "critical": by_priority.get(1, 0),
            "high": by_priority.get(2, 0),
            "medium": by_priority.get(3, 0),
            "low": by_priority.get(4, 0),
            "minimal": by_priority.get(5, 0),
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def build_user_report(user_id):
    from src.controllers.task_controller import compute_overdue

    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    reference = now_utc()
    tasks = Task.query.filter_by(user_id=user_id).all()
    counters = {"done": 0, "pending": 0, "in_progress": 0, "cancelled": 0}
    overdue = 0
    high_priority = 0
    for t in tasks:
        if t.status in counters:
            counters[t.status] += 1
        if t.priority is not None and t.priority <= 2:
            high_priority += 1
        if compute_overdue(t, reference):
            overdue += 1
    total = len(tasks)
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            **counters,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((counters["done"] / total) * 100, 2) if total > 0 else 0,
        },
    }
