from sqlalchemy import func

from src.errors import NotFoundError
from src.models import db
from src.models.category import Category
from src.models.task import Task
from src.schemas import validate_with
from src.schemas.category_schema import CategorySchema

_category_schema = CategorySchema()


def list_categories():
    rows = (
        db.session.query(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .all()
    )
    result = []
    for cat, task_count in rows:
        data = cat.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result


def create_category(payload):
    data = validate_with(_category_schema, payload)
    cat = Category()
    cat.name = data["name"]
    cat.description = data.get("description", "")
    cat.color = data.get("color")
    db.session.add(cat)
    db.session.commit()
    return cat.to_dict()


def update_category(category_id, payload):
    cat = db.session.get(Category, category_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    data = validate_with(_category_schema, payload, partial=True)
    if "name" in data:
        cat.name = data["name"]
    if "description" in data:
        cat.description = data["description"]
    if "color" in data:
        cat.color = data["color"]
    db.session.commit()
    return cat.to_dict()


def delete_category(category_id):
    cat = db.session.get(Category, category_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    db.session.delete(cat)
    db.session.commit()
    return {"message": "Categoria deletada"}
