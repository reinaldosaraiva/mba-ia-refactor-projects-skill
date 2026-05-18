"""Health and welcome endpoints."""
from flask import Blueprint, jsonify

from src.controllers import health_controller
from src.views.response import success

health_bp = Blueprint("health", __name__)


@health_bp.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "2.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


@health_bp.route("/health")
def health():
    return success(health_controller.check())
