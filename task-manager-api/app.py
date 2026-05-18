import logging

from flask import Flask
from flask_cors import CORS

from src.config import settings
from src.middlewares.error_handler import register as register_error_handlers
from src.models import db
from src.utils.helpers import now_utc
from src.views import register_blueprints
from src.views.response import success


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.SECRET_KEY

    CORS(app)
    db.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    @app.route("/health")
    def health():
        return success({"status": "ok", "timestamp": str(now_utc())})

    @app.route("/")
    def index():
        return success({"message": "Task Manager API", "version": "1.0"})

    with app.app_context():
        # Import model modules so SQLAlchemy registers their mappers.
        import src.models.category  # noqa: F401
        import src.models.task  # noqa: F401
        import src.models.user  # noqa: F401

        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
