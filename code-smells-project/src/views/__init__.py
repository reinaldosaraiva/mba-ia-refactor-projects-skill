"""Blueprint registration helper."""
from src.views.produto_routes import produto_bp
from src.views.usuario_routes import usuario_bp
from src.views.pedido_routes import pedido_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.health_routes import health_bp


def register_blueprints(app):
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(health_bp)
