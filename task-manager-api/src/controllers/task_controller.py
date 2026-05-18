from sqlalchemy.orm import joinedload

from src.config.constants import TERMINAL_STATUSES
from src.errors import NotFoundError, ValidationError
from src.models import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.schemas import validate_with
from src.schemas.task_schema import TaskSchema, normalise_tags, parse_due_date
from src.utils.helpers import now_utc

_task_schema = TaskSchema()


def compute_overdue(task, reference=None):
    if not task.due_date:
        return False
    ref = reference if reference is not None else now_utc()
    if task.due_date >= ref:
        return False
    return task.status not in TERMINAL_STATUSES


def _serialise(task, reference):
    data = task.to_dict()
    data["overdue"] = compute_overdue(task, reference)
    data["user_name"] = task.user.name if task.user is not None else None
    data["category_name"] = task.category.name if task.category is not None else None
    return data


def _assert_user_exists(user_id):
    if user_id is not None and db.session.get(User, user_id) is None:
        raise NotFoundError("Usuário não encontrado")


def _assert_category_exists(category_id):
    if category_id is not None and db.session.get(Category, category_id) is None:
        raise NotFoundError("Categoria não encontrada")


def list_tasks():
    reference = now_utc()
    tasks = (
        Task.query
        .options(joinedload(Task.user), joinedload(Task.category))
        .all()
    )
    return [_serialise(t, reference) for t in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError(f"Task {task_id} não encontrada")
    data = task.to_dict()
    data["overdue"] = compute_overdue(task)
    return data


def create_task(payload):
    data = validate_with(_task_schema, payload)
    _assert_user_exists(data.get("user_id"))
    _assert_category_exists(data.get("category_id"))

    task = Task()
    task.title = data["title"]
    task.description = data.get("description", "")
    task.status = data.get("status", "pending")
    task.priority = data.get("priority")
    task.user_id = data.get("user_id")
    task.category_id = data.get("category_id")
    task.due_date = parse_due_date(data.get("due_date"))
    task.tags = normalise_tags(data.get("tags"))

    db.session.add(task)
    db.session.commit()
    return task.to_dict()


def update_task(task_id, payload):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError(f"Task {task_id} não encontrada")

    data = validate_with(_task_schema, payload, partial=True)

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]
    if "priority" in data:
        task.priority = data["priority"]
    if "user_id" in data:
        _assert_user_exists(data["user_id"])
        task.user_id = data["user_id"]
    if "category_id" in data:
        _assert_category_exists(data["category_id"])
        task.category_id = data["category_id"]
    if "due_date" in data:
        task.due_date = parse_due_date(data["due_date"])
    if "tags" in data:
        task.tags = normalise_tags(data["tags"])

    task.updated_at = now_utc()
    db.session.commit()
    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError(f"Task {task_id} não encontrada")
    db.session.delete(task)
    db.session.commit()
    return {"message": "Task deletada com sucesso"}


def _coerce_int(value, field):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} deve ser inteiro")


def search_tasks(filters):
    query = (
        Task.query
        .options(joinedload(Task.user), joinedload(Task.category))
    )
    term = filters.get("q")
    status = filters.get("status")
    priority = _coerce_int(filters.get("priority"), "priority")
    user_id = _coerce_int(filters.get("user_id"), "user_id")

    if term:
        like = f"%{term}%"
        query = query.filter(db.or_(Task.title.like(like), Task.description.like(like)))
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)

    return [t.to_dict() for t in query.all()]


def task_stats():
    from sqlalchemy import func

    reference = now_utc()
    total = db.session.query(func.count(Task.id)).scalar() or 0
    by_status = dict(
        db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    overdue = (
        db.session.query(func.count(Task.id))
        .filter(Task.due_date.isnot(None))
        .filter(Task.due_date < reference)
        .filter(~Task.status.in_(list(TERMINAL_STATUSES)))
        .scalar()
        or 0
    )
    done = by_status.get("done", 0)
    return {
        "total": total,
        "pending": by_status.get("pending", 0),
        "in_progress": by_status.get("in_progress", 0),
        "done": done,
        "cancelled": by_status.get("cancelled", 0),
        "overdue": overdue,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }
