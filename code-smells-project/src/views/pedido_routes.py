"""Pedido HTTP endpoints."""
from flask import Blueprint, request

from src.controllers import pedido_controller
from src.views.response import success

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar():
    result = pedido_controller.criar(request.get_json())
    return success(result, message="Pedido criado com sucesso", http=201)


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos():
    return success(pedido_controller.listar_todos())


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_por_usuario(usuario_id):
    return success(pedido_controller.listar_por_usuario(usuario_id))


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status(pedido_id):
    pedido_controller.atualizar_status(pedido_id, request.get_json())
    return success(message="Status atualizado")
