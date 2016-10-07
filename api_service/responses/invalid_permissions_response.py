import json

from flask import make_response


def invalid_permissions_response(message, permissions):
    data = {
        "message": message,
        "permissions": permissions
    }
    response = make_response(json.dumps(data), 400)
    response.headers['Content-type'] = "application/json"
    return response
