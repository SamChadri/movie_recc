from json import load
import sys
import json
from flask.wrappers import Response
import os
import time
from .ml_backend.recc import Reccomender
from .ml_backend.movielens import Rating
import functools
from celery import Celery
from datetime import datetime
from .celery_utils import make_celery
from multiprocessing import Process, Manager
from .ml_backend.postgres.movielens_store import MovieLensStore
from .ml_backend.postgres.user_auth import UserAuthStore
import logging
import copy
import multiprocessing as mp
from gevent import monkey
from multiprocessing import Pool
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, stream_with_context, current_app, render_template_string
)

class ReccBlueprint:

    def __init__(self):
        self.logger = logging.getLogger('gunicorn.error')
        self.user_id = 610
        self.movie_posters = []
        self.task = None
        self.inserted_ratings = []
        self.inserted_user = None
        self.recc = Reccomender()

    def create_shared_list(self):
        self.recc_results = Manager().list()

    def get_shared_list(self):
        return self.recc_results


TAG = 'ReccBluePrint'
bp = Blueprint('recc', __name__, url_prefix='/recc')
#recc = Reccomender()

#logger = current_app.logger
logger = logging.getLogger('gunicorn.error')
celery = make_celery()
user_id = 610
movie_posters = []
task = None
inserted_ratings = []
user_list = None
#recc_results = Manager().list()
load_task = None
inserted_user = None
recc_bp = ReccBlueprint()
sample_data = {
    'processes': 4,
    'chunksize': 1,
    'total_size': 943,
    'curr_user': 1,
    'records_affected': 1
}

def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))

def process_test(x):
    logger = logging.getLogger('gunicorn.error')
    logger.info(f'{TAG}:: Running test func with number {x}')
    print(f'{TAG}:: Running test func with number {x}')
    for num in range(x):
        logger.info(f'{TAG}:: Result: {num + num}')
        print(f'{TAG}:: Result: {num + num}')
        time.sleep(1)


def load_pcs(user_list, postgres_ip, postgres_port, x, modern=False):
    logger = logging.getLogger('gunicorn.error')
    logger.info(f'{TAG}:: Running test func with number {x}')
    #print(f'{TAG}:: Running test func with number {x}')
    for num in range(x):
        logger.info(f'{TAG}:: Result: {num*num}')
        #print(f'{TAG}:: Result: {num*num}')
        time.sleep(1)
    if modern:
        MovieLensStore.load_modern_user_pcs_data(user_list, postgres_ip, postgres_port, MovieLensStore.event_queue)
        MovieLensStore.get_db().pcs_loaded = True
    else:
        MovieLensStore.load_user_pcs_data(user_list, postgres_ip, postgres_port, MovieLensStore.event_queue)
        MovieLensStore.get_db().modern_pcs_loaded = True
    #with Pool(processes=2) as pool:
    #    logger.info(f'{TAG}:: Starting pool of workers for map function...')
    #    pool.map_async(func=process_test, iterable=range(5))
    #    #pool.map(func=process_test, iterable=range(5))




@bp.route("/load_data", methods=["GET"])
def load_data():

    return render_template('ui_load_data.html',users=user_list, last_updated=dir_last_updated('flaskr/static/'))


@bp.route("/get_credentials", methods=["POST"])
def get_credentials():
    auth_db = UserAuthStore.get_auth_store()
    if request.method == "POST":
        email = request.form["email"]
        credentials = auth_db.get_user(email, UserAuthStore.EMAIL)


    return credentials.__dict__

@bp.route("/register_credentials", methods=["POST"])
def register_credentials():
    auth_db = UserAuthStore.get_auth_store()
    if request.method == "POST":
        email = request.form["email"]
        pass_hash = request.form["password_hash"]
        user_key = auth_db.insert_user(email, pass_hash)
        #Register user here in the movielens store
    
    
    

@bp.route("/load_modern_data", methods=["GET"])
def load_modern_data():
    load_task.terminate()
    return render_template('ui_load_modern_data.html',users=user_list, last_updated=dir_last_updated('flaskr/static/'))

@bp.route("/load_pcs_data", methods=["GET"])
def load_pcs_data():
    global user_list
    global load_task
    moveieLens_db = MovieLensStore.get_db()
    postgres_ip = copy.deepcopy(moveieLens_db.postgres_ip)
    postgres_port = copy.deepcopy(moveieLens_db.postgres_port) 
    user_list, _ = MovieLensStore.get_db().get_all_users()
    load_task = Process(target=load_pcs, args=(user_list,postgres_ip, postgres_port,10, False))
    load_task.start()
    def generator():
        logger.info(f'{TAG}:: Starting generator...')
        while sample_data['records_affected'] < 100:
            #data = f'data: {json.dumps(sample_data)}\n\n'
            data = MovieLensStore.event_queue.get()
            logger.info(f'{TAG}:: Streaming data {data}')
            yield data
            #sample_data['records_affected'] += 1
            #time.sleep(1)
    
    return Response(generator(), mimetype='text/event-stream')

@bp.route("/load_modern_pcs_data", methods=["GET"])
def load_modern_pcs_data():
    global user_list
    global load_task
    moveieLens_db = MovieLensStore.get_db()
    postgres_ip = copy.deepcopy(moveieLens_db.postgres_ip)
    postgres_port = copy.deepcopy(moveieLens_db.postgres_port) 
    user_list, _ = MovieLensStore.get_db().get_all_modern_users()
    load_task = Process(target=load_pcs, args=(user_list,postgres_ip, postgres_port,10, True))
    load_task.start()
    def generator():
        logger.info(f'{TAG}:: Starting generator...')
        while sample_data['records_affected'] < 100:
            #data = f'data: {json.dumps(sample_data)}\n\n'
            data = MovieLensStore.event_queue.get()
            logger.info(f'{TAG}:: Streaming data {data}')
            yield data
            #sample_data['records_affected'] += 1
            #time.sleep(1)
    
    return Response(generator(), mimetype='text/event-stream')

@bp.route("/movies", methods=["GET"])
def create_user():
    recc_bp.user_id += 1
    exists = recc_bp.recc.check_user(recc_bp.user_id, recc_bp.inserted_user)
    if not exists:
        recc_bp.recc.insert_user(recc_bp.user_id)
        logger.info(f'{TAG}: User inserted with id: {recc_bp.user_id}')
    

    session['user_id'] = recc_bp.user_id

    return render_template('ui_recc.html')



@bp.route("/movies", methods=['POST'])
def submit_rating():
    if request.method == "POST":
        recc_bp.recc.insert_rating(user_id, request.form["itemId"], request.form["rating"],  datetime.today().isoformat(timespec='seconds') )
        entry = {}
        entry["user_id"] = user_id
        entry["item_id"] = request.form["itemId"]
        entry["rating"] = request.form["rating"]
        entry["time"] = datetime.today().isoformat(timespec='seconds')
        session[request.form["itemId"]] = request.form["rating"]
        inserted_ratings.append(entry)        
        logger.info(f"{TAG}: Rating inserted. Rating: {request.form['rating']}, ID: {request.form['itemId']}")

    return '', 204


@bp.route('/await_response', methods=["GET"])
def generate_response():
    logger.info(f'{TAG} waiting for child process reccomendations...')
    task.join()
    logger.info(f'{TAG} reccomender sub-process finished')
    return redirect(url_for('recc.recc_list'))
    

@bp.route("/load", methods=["GET"])
def load_recc():
    global user_id
    global task
    #global recc_results
    logger.info(f'{TAG}: Generating reccomendations for user: {user_id}')
    recc_bp.create_shared_list()
    task = Process(target=generate_recc, args=(user_id, inserted_ratings, recc_bp.get_shared_list()))
    task.start()
    session["task"] = task.name
    logger.info( f'{TAG}: Task generated with id: {task.name}')

    return render_template('ui_loading.html')
    
    


#TODO: Implement loading bar
def generate_recc(user_id, ratings, results):
    recc_bp.recc.insert_user(user_id)
    entries = []
    for rating in ratings:
        entries.append(Rating(rating["user_id"], rating["item_id"], rating["rating"], rating["time"]))
    recc_bp.recc.get_new_ratings().extend(entries)
    recc_bp.recc.get_modernUser_ratings()[user_id] = entries
    movie_ids = recc_bp.recc.reccomend(user_id)
    logger.info(f'{TAG}: Length of movie ids ={ len(movie_ids)}')
    recc_bp.recc.imdb_req(movie_ids, results)
    logger.info(f'{TAG}: Posters Done. Number of results = {len(results)}')

@bp.route('/recc_list', methods=["GET"])
def recc_list():
    global task
    logger.info(f'{TAG} waiting for child process reccomendations...')
    task.join()
    recc_results = recc_bp.get_shared_list()
    logger.info(f'{TAG}: reccomender sub-process finished. Creating posters with {len(recc_results)} posters')
    movie_posters = recc_bp.recc.create_poster(recc_results)
    logger.info(f'{TAG}: Created {len(movie_posters)} posters')
    session["len_movies"] = len(movie_posters)
    print(len(movie_posters))
    return render_template('ui_results.html', movies=movie_posters)
    