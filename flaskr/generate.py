import sys


from .ml_backend import recc
import functools
from celery import Celery
from datetime import datetime
from .celery_utils import make_celery

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)


bp = Blueprint('recc', __name__, url_prefix='/recc')
celery = make_celery()
user_id = 610
movie_posters = []
global task
inserted_ratings = []
inserted_user = None

@bp.route("/movies", methods=["GET"])
def create_user():
    global user_id
    user_id += 1
    recc.insert_user(user_id)
    exists = recc.check_user(user_id, inserted_user)
    session['user_id'] = user_id
    if(exists):
        print("User inserted with id: " + str(user_id))
    return render_template('ui_recc.html')



@bp.route("/movies", methods=['POST'])
def submit_rating():
    if request.method == "POST":
        print(request.form["rating"])
        recc.insert_rating(user_id, request.form["itemId"], request.form["rating"],  datetime.today().isoformat(timespec='seconds') )
        entry = {}
        entry["user_id"] = user_id
        entry["item_id"] = request.form["itemId"]
        entry["rating"] = request.form["rating"]
        entry["time"] = datetime.today().isoformat(timespec='seconds')
        session[request.form["itemId"]] = request.form["rating"]
        inserted_ratings.append(entry)        
        print("Rating inserted", " Rating: " + str(request.form["rating"]), "ID: " + str(str(request.form["itemId"])))

    return '', 204
    

@bp.route("/load", methods=["GET"])
def load_recc():
    global user_id
    global task
    print("Generating reccomendations for user: " + str(user_id))
    result = generate_recc.delay(user_id, inserted_ratings)
    task = result
    session["task"] = task.id
    print( "Task generated with id: " + str(task.id))
    return render_template('ui_loading.html')



@celery.task
def generate_recc(user_id, ratings):
    recc.insert_user(user_id)
    entries = []
    for rating in ratings:
        entries.append(recc.Rating(rating["user_id"], rating["item_id"], rating["rating"], rating["time"]))
    recc.new_ratings.extend(entries)
    recc.modernUser_ratings[user_id] = entries
    movie_ids = recc.reccomend(user_id)
    movie_posters = recc.imdb_req(movie_ids)
    print("Posters Done")
    print(len(movie_posters))
    return movie_posters

@bp.route('/recc_list', methods=["GET"])
def recc_list():
    global task
    print(task.info)
    movie_posters = recc.create_poster(task.info)
    session["len_movies"] = len(movie_posters)
    print(len(movie_posters))
    return render_template('ui_results.html', movies=movie_posters)
    