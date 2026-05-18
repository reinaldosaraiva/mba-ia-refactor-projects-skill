"""Composition root for the e-commerce API.

Builds the Flask instance, wires CORS, registers blueprints, registers the
error handler, initialises the database. No business logic here.
"""
from flask import Flask
from flask_cors import CORS

from src.config import settings
from src.middlewares import error_handler
from src.models import init_db
from src.views import register_blueprints


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app)
    init_db(app)
    register_blueprints(app)
    error_handler.register(app)
    return app


app = create_app()


if __name__ == "__main__":
    print(f"Servidor iniciando em http://{settings.HOST}:{settings.PORT}")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
