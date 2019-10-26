import sys
import time
import random
from .part2 import *
import requests as req
from requests.exceptions import HTTPError

class MoviePoster:
    def __init__(self, title, poster, plot, genre):
        self.title = title
        self.poster = poster
        self.plot = plot
        self.genre = genre


def insert_rating(user_id, item_id, rating, time):
    rating = Rating(user_id, item_id, rating, time)
    new_ratings.append(rating)
    modernUser_ratings[user_id].append(rating)

def insert_user(user_id):
    new_users.append(ModernUser(user_id))
    modernUser_ratings[user_id] = []

def check_user(user_id, inserted_user):
    s_user = None
    for u in new_users:
        if user_id == u.id:
            s_user = u
            break
    if type(s_user) == type(None):
        return False
    else:
        inserted_user = s_user

        return True

def reccomend(user_id):
    predictions = {}
    cluster_num = 1
    movie_samples = random.choices(modernItem_clusters[cluster_num], k=100)
    bar = Bar('Generating Predictions', max = len(movie_samples), suffix = '%(percent).1f%%')
    for item in movie_samples:
        rating = round(updated_guess(user_id, item.id, 150), 5)
        predictions[Link.id_links[item.id]] = rating
        bar.next()
    bar.finish()
    val =  sorted(predictions, key=predictions.__getitem__)
    val = val[0:5]
    return val

def imdb_req(title_ids):
    movie_posters = []
    url = "http://www.omdbapi.com/?apikey=3a942993&i="
    prefix = ['tt', 'nm', 'co', 'ev', 'ch','ni']
    for id in title_ids:
        for s in prefix:
            try:
                response = req.get(url+s+str(id))
                response.raise_for_status()
                if response.json()["Response"] == "True":
                    entry = {}
                    entry["Title"] = response.json()["Title"]
                    entry["Poster"] = response.json()["Poster"]
                    entry["Plot"] = response.json()["Plot"]
                    entry["Genre"] = response.json()["Genre"]
                    movie_posters.append(entry)
            except HTTPError as http_err:
                print(f'HTTP error occurred: {http_err}')
            except Exception as err:
                print(f'Other error occured: {err}')


    return movie_posters 


def create_poster(entries):
    posters = []
    for entry in entries:
        posters.append(MoviePoster(entry["Title"], entry["Poster"], entry["Plot"], entry["Genre"]))
    return posters