from marshmallow import ValidationError as _MMValidationError

from src.errors import ValidationError


def validate_with(schema, data, partial=False):
    try:
        return schema.load(data or {}, partial=partial)
    except _MMValidationError as exc:
        first_field, messages = next(iter(exc.messages.items()))
        message = messages[0] if isinstance(messages, list) else str(messages)
        raise ValidationError(f"{first_field}: {message}")
