import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger("task-manager-api")


def _envelope(code, message, http):
    return jsonify({
        "status": "error",
        "error": {"code": code, "message": message},
    }), http


def register(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        logger.warning("AppError %s: %s", exc.code, exc.message)
        return _envelope(exc.code, exc.message, exc.http)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return _envelope(exc.name.lower().replace(" ", "_"), exc.description, exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logger.exception("Unhandled exception")
        return _envelope("internal_error", "Internal server error", 500)
