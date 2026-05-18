from flask import Blueprint, request

from src.controllers import category_controller
from src.views.response import success

category_bp = Blueprint("categories", __name__)


@category_bp.route("/categories", methods=["GET"])
def list_categories():
    return success(category_controller.list_categories())


@category_bp.route("/categories", methods=["POST"])
def create_category():
    return success(category_controller.create_category(request.get_json(silent=True)), http=201)


@category_bp.route("/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    return success(category_controller.update_category(category_id, request.get_json(silent=True)))


@category_bp.route("/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    return success(category_controller.delete_category(category_id))
