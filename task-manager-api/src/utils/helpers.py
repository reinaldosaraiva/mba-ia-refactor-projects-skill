import re
from datetime import datetime, timezone


def now_utc():
    """Naive UTC datetime — replaces deprecated ``datetime.utcnow()``."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", email or ""))


def sanitize_string(s):
    return s.strip() if s else s


def parse_date(date_string):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


def is_valid_color(color):
    return bool(color and len(color) == 7 and color[0] == "#")
