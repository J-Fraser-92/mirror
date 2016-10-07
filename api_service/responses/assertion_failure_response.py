import json

from flask import make_response


def assertion_failure_response():
    data = {
        "message": "An internal error occurred, and has been raised with TAS. Sorry for the inconvenience."
    }
    response = make_response(json.dumps(data), 500)
    response.headers['Content-type'] = "application/json"
    return response
