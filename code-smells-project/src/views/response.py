"""Canonical JSON response envelope helpers."""
from flask import jsonify


def success(data=None, message=None, http=200):
    payload = {"status": "ok", "sucesso": True}
    if data is not None:
        payload["dados"] = data
    if message is not None:
        payload["mensagem"] = message
    return jsonify(payload), http


def error(message, code="error", http=500):
    return jsonify({
        "status": "error",
        "sucesso": False,
        "erro": message,
        "code": code,
    }), http
