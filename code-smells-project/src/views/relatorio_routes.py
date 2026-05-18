"""Sales report endpoint."""
from flask import Blueprint

from src.controllers import relatorio_controller
from src.views.response import success

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
def vendas():
    return success(relatorio_controller.vendas())
