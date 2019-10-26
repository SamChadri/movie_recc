import os
import sys
from flask import Flask
from flask import render_template

def create_app(test_config=None):
    #create and configure app
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )
    app.config['CELERY_BROKER_URL'] = 'amqp://localhost'
    app.config['RESULT_BACKEND'] = 'amqp://localhost'

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    from . import generate
    app.register_blueprint(generate.bp)

    from . import celery_utils
    celery_utils.init_celery(app, generate.celery)
    

    @app.route('/')
    def home():
        return render_template('ui_home.html')
    return app