from sqlalchemy.orm import joinedload

from src.errors import (
    AuthError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from src.models import db
from src.models.task import Task
from src.models.user import User
from src.schemas import validate_with
from src.schemas.user_schema import UserSchema

_user_schema = UserSchema()


def list_users():
    users = User.query.options(joinedload(User.tasks)).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "active": u.active,
            "created_at": str(u.created_at),
            "task_count": len(u.tasks),
        }
        for u in users
    ]


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = user.to_dict()
    data["tasks"] = [t.to_dict() for t in user.tasks]
    return data


def create_user(payload):
    data = validate_with(_user_schema, payload)
    if User.query.filter_by(email=data["email"]).first():
        raise ConflictError("Email já cadastrado")
    user = User()
    user.name = data["name"]
    user.email = data["email"]
    user.set_password(data["password"])
    user.role = data.get("role", "user")
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def update_user(user_id, payload):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = validate_with(_user_schema, payload, partial=True)

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = data["email"]
    if "password" in data:
        user.set_password(data["password"])
    if "role" in data:
        user.role = data["role"]
    if "active" in data:
        user.active = data["active"]

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    db.session.delete(user)
    db.session.commit()
    return {"message": "Usuário deletado com sucesso"}


def get_user_tasks(user_id):
    from src.controllers.task_controller import compute_overdue
    from src.utils.helpers import now_utc

    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    reference = now_utc()
    tasks = (
        Task.query
        .filter_by(user_id=user_id)
        .all()
    )
    result = []
    for t in tasks:
        data = t.to_dict()
        data["overdue"] = compute_overdue(t, reference)
        result.append(data)
    return result


def authenticate(payload):
    if not payload:
        raise ValidationError("Dados inválidos")
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    # Residual (v1 scope): real JWT signing is not yet implemented; token is
    # a deterministic placeholder so existing clients keep working.
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": "fake-jwt-token-" + str(user.id),
    }
