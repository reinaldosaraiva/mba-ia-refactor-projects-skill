from datetime import datetime

from marshmallow import EXCLUDE, Schema, fields, validate

from src.config.constants import (
    TASK_DEFAULT_PRIORITY,
    TASK_PRIORITY_MAX,
    TASK_PRIORITY_MIN,
    TASK_TITLE_MAX_LEN,
    TASK_TITLE_MIN_LEN,
    VALID_STATUSES,
)
from src.errors import ValidationError


class TaskSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(
        required=True,
        validate=validate.Length(min=TASK_TITLE_MIN_LEN, max=TASK_TITLE_MAX_LEN),
    )
    description = fields.String(load_default="")
    status = fields.String(
        load_default="pending",
        validate=validate.OneOf(VALID_STATUSES),
    )
    priority = fields.Integer(
        load_default=TASK_DEFAULT_PRIORITY,
        validate=validate.Range(min=TASK_PRIORITY_MIN, max=TASK_PRIORITY_MAX),
    )
    user_id = fields.Integer(load_default=None, allow_none=True)
    category_id = fields.Integer(load_default=None, allow_none=True)
    due_date = fields.String(load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)


def parse_due_date(value):
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("due_date: formato inválido, use YYYY-MM-DD")


def normalise_tags(tags):
    if tags is None:
        return None
    if isinstance(tags, list):
        return ",".join(str(t) for t in tags)
    return str(tags)
