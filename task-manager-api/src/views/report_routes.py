from flask import Blueprint

from src.controllers import report_controller
from src.views.response import success

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
def summary_report():
    return success(report_controller.build_summary())


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    return success(report_controller.build_user_report(user_id))
