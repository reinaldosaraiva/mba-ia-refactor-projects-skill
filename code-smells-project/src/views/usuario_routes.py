"""Usuario HTTP endpoints."""
from flask import Blueprint, request

from src.controllers import usuario_controller
from src.views.response import success

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar():
    return success(usuario_controller.listar())


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def detalhar(usuario_id):
    return success(usuario_controller.detalhar(usuario_id))


@usuario_bp.route("/usuarios", methods=["POST"])
def criar():
    result = usuario_controller.criar(request.get_json())
    return success(result, http=201)


@usuario_bp.route("/login", methods=["POST"])
def login():
    user = usuario_controller.login(request.get_json())
    return success(user, message="Login OK")
