from marshmallow import EXCLUDE, Schema, fields, validate

from src.config.constants import CATEGORY_DEFAULT_COLOR


class CategorySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(load_default="")
    color = fields.String(
        load_default=CATEGORY_DEFAULT_COLOR,
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"),
    )
