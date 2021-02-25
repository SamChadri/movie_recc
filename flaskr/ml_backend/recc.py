from flaskr.ml_backend.postgres.movielens_store import MovieLensStore
import sys
import time
import random
from .part2 import ReccEngine
import requests as req
from requests.exceptions import HTTPError
from .movielens import *
from progress.bar import ChargingBar as Bar
import logging


class MoviePoster:
    def __init__(self, title, poster, plot, genre):
        self.title = title
        self.poster = poster
        self.plot = plot
        self.genre = genre


engine_init = False
TAG = 'Reccomender'
class Reccomender:
    
    def __init__(self):
        global engine_init
        self.logger = logging.getLogger('gunicorn.error')
        self.engine = ReccEngine()
        self.movielens_db = MovieLensStore.get_db()
        if not engine_init:
            if not MovieLensStore.instance_init:
                self.engine.load_user_data()
                self.engine.clutser_data()
            else:
                self.engine.cluster_new_data()
            engine_init = True
            self.logger.info(f'{TAG} Reccomender engine initialized. Setting engine_init param to True')

      
    def insert_rating(self, user_id, item_id, rating, time):
        rating = Rating(user_id, item_id, rating, time)
        self.engine.new_ratings.append(rating)
        #self.engine.modernUser_ratings[user_id].append(rating)
        self.movielens_db.insert_rating(rating)

    def get_new_ratings(self):
        return self.movielens_db.get_all_modern_ratings()
        #return self.engine.new_ratings

    def get_modernUser_ratings(self):
        #return self.engine.modernUser_ratings
        return self.movielens_db.get_all_modern_ratings()

    def insert_user(self,user_id):
        self.engine.new_users.append(ModernUser(user_id))
        self.engine.modernUser_ratings[user_id] = []

        self.movielens_db.insert_user(ModernUser(user_id))

    def check_user(self, user_id, inserted_user):
        self.logger.info(f'{TAG}: Checking to see if user exists....')
        s_user = None
        s_user = self.movielens_db.get_modern_user(user_id)
        #for u in self.engine.new_users:
        #    if user_id == u.id:
        #        s_user = u
        #        break
        if type(s_user) == type(None):
            self.logger.info(f'{TAG}: Could not find user. Creating new user entry.')
            return False
        else:
            self.logger.info(f'{TAG}: Found user. Setting param to found user. ')
            inserted_user = s_user

            return True

    def reccomend(self, user_id):
        predictions = {}
        cluster_num = 1
        #This number can be changed once one can really test with the PCS data.
        movie_samples = random.choices(self.engine.modernItem_clusters[cluster_num], k=200)
        bar = Bar('Generating Predictions', max = len(movie_samples), suffix = '%(percent).1f%%')
        for item in movie_samples:
            rating = round(self.engine.new_guess(user_id, item.id, 150), 5)
            #predictions[Link.id_links[item.id]] = rating
            predictions[self.movielens_db.get_link(item.id)] = rating
            bar.next()
        bar.finish()
        val =  sorted(predictions, key=predictions.__getitem__)
        val = val[0:5]
        return val

    def imdb_req(self, title_ids, movie_results):
        movie_posters = []
        url = "http://www.omdbapi.com/?apikey=3a942993&i={}"
        prefix = ['tt', 'nm', 'co', 'ev', 'ch','ni']
        self.logger.info(f'{TAG}: Movie IDs: {title_ids}')
        for id in title_ids:
            for s in prefix:
                try:
                    padded_id = str(id).zfill(7)
                    imdb_id = f'{s}{padded_id}'
                    self.logger.info(f'{TAG} url = {url.format(imdb_id)}')
                    response = req.get(url.format(imdb_id))
                    response.raise_for_status()
                    if response.text.find('"Response":"False"') != 1:
                        entry = {}
                        entry["Title"] = response.json()["Title"]
                        entry["Poster"] = response.json()["Poster"]
                        entry["Plot"] = response.json()["Plot"]
                        entry["Genre"] = response.json()["Genre"]
                        movie_results.append(entry)
                        self.logger.info(f'{TAG}: Added new movie poster entry')
                        break
                except HTTPError as http_err:
                    self.logger.info(f'{TAG}: HTTP error occurred: {http_err}')
                except Exception as err:
                    self.logger.info(f'{TAG}: Other error occured: {err}')

        self.logger.info(f'{TAG}: Movie Poster results: {movie_posters}')
        #return movie_results 


    def create_poster(self,entries):
        posters = []
        for entry in entries:
            posters.append(MoviePoster(entry["Title"], entry["Poster"], entry["Plot"], entry["Genre"]))
        return posters