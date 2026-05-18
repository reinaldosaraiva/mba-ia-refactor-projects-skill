from marshmallow import EXCLUDE, Schema, fields, validate

from src.config.constants import USER_PASSWORD_MIN_LEN, VALID_ROLES


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=validate.Length(min=USER_PASSWORD_MIN_LEN),
    )
    role = fields.String(load_default="user", validate=validate.OneOf(VALID_ROLES))
    active = fields.Boolean()
