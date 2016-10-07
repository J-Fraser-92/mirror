#!flask/bin/python
from api_service import application
from api_service import flask_service

application.run(debug=False, host='0.0.0.0', use_reloader=True)
