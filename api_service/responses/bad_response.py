import json

from flask import make_response


def bad_response(message):
    data = {
        "message": message
    }
    response = make_response(json.dumps(data), 400)
    response.headers['Content-type'] = "application/json"
    return response
