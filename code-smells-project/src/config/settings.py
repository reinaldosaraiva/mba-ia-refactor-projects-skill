"""Environment-loaded application settings.

Secrets have no default — the app fails fast if SECRET_KEY is missing.
Non-sensitive flags have safe defaults so the app boots in dev.
"""
import os

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
