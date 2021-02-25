from flaskr.ml_backend.postgres.movielens_store import MovieLensStore
import os
import sys
from flask import Flask
from flask import render_template, redirect, url_for
from logging.config import dictConfig
import logging
import multiprocessing as mp
from multiprocessing import Pool
from flask_cors import CORS


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

    app.logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.handlers.clear()
    app.logger.addHandler(handler)

    app.logger.info(f'Testing Log')


    #pool = mp.get_context('spawn').Pool(processes=2)

    #app.config['workers'] = pool
    with app.app_context():
        from . import generate
        app.register_blueprint(generate.bp)
        MovieLensStore.init_db()

    from . import celery_utils
    celery_utils.init_celery(app, generate.celery)

    CORS(app)
    
    @app.route('/')
    def home():

        pcs_init = MovieLensStore.get_db().pcs_loaded and MovieLensStore.get_db().modern_pcs_loaded
        if not pcs_init:
            return redirect(url_for('recc.load_data'))
        
        return render_template('ui_home.html')
    return app