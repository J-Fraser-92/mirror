from flask import request, render_template

from api_service import application

@application.route('/', methods=['GET'])
def call_home():
    return render_template('home.html')
