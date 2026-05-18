from flask import jsonify


def success(data=None, message=None, http=200):
    payload = {"status": "ok"}
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    return jsonify(payload), http
