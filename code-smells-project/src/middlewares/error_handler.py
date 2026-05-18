"""Centralised error handler. Maps AppError subclasses to HTTP envelopes."""
import logging
from flask import current_app

from src.errors import AppError
from src.views.response import error


def register(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        current_app.logger.info("AppError: %s", exc)
        return error(str(exc) or exc.code, code=exc.code, http=exc.http)

    @app.errorhandler(404)
    def handle_404(_exc):
        return error("Recurso não encontrado", code="not_found", http=404)

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logging.exception("Unhandled exception")
        return error("Internal Server Error", code="internal_error", http=500)
