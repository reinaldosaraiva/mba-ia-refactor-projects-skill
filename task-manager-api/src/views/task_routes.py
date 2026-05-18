from flask import Blueprint, request

from src.controllers import task_controller
from src.views.response import success

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def list_tasks():
    return success(task_controller.list_tasks())


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return success(task_controller.get_task(task_id))


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    return success(task_controller.create_task(request.get_json(silent=True)), http=201)


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    return success(task_controller.update_task(task_id, request.get_json(silent=True)))


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    return success(task_controller.delete_task(task_id))


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    filters = {
        "q": request.args.get("q"),
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "user_id": request.args.get("user_id"),
    }
    return success(task_controller.search_tasks(filters))


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return success(task_controller.task_stats())
