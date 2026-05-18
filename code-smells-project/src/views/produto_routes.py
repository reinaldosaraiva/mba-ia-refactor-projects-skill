"""Produto HTTP endpoints."""
from flask import Blueprint, request

from src.controllers import produto_controller
from src.views.response import success

produto_bp = Blueprint("produtos", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar():
    return success(produto_controller.listar())


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar():
    resultados = produto_controller.buscar(
        termo=request.args.get("q") or None,
        categoria=request.args.get("categoria") or None,
        preco_min=request.args.get("preco_min"),
        preco_max=request.args.get("preco_max"),
    )
    return success({"resultados": resultados, "total": len(resultados)})


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def detalhar(produto_id):
    return success(produto_controller.detalhar(produto_id))


@produto_bp.route("/produtos", methods=["POST"])
def criar():
    result = produto_controller.criar(request.get_json())
    return success(result, message="Produto criado", http=201)


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar(produto_id):
    produto_controller.atualizar(produto_id, request.get_json())
    return success(message="Produto atualizado")


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar(produto_id):
    produto_controller.deletar(produto_id)
    return success(message="Produto deletado")
