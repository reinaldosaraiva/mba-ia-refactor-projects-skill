from flask import Blueprint, request

from src.controllers import user_controller
from src.views.response import success

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def list_users():
    return success(user_controller.list_users())


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return success(user_controller.get_user(user_id))


@user_bp.route("/users", methods=["POST"])
def create_user():
    return success(user_controller.create_user(request.get_json(silent=True)), http=201)


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    return success(user_controller.update_user(user_id, request.get_json(silent=True)))


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return success(user_controller.delete_user(user_id))


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return success(user_controller.get_user_tasks(user_id))


@user_bp.route("/login", methods=["POST"])
def login():
    return success(user_controller.authenticate(request.get_json(silent=True)))
