#!/bin/python
from progress.bar import ChargingBar as Bar
import itertools
import math
from functools import reduce
from .movielens import *
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from .cluster import *
from datetime import datetime
import sys
import time
import random
import os
import logging
from .postgres.movielens_store import MovieLensStore
from flask import current_app
update = True
import sys

TAG = 'ReccEngine'

if len(sys.argv) > 1 :
    if sys.argv[1] == "-u":
        update = False

class ReccEngine:
    
    def __init__(self, update=True):
        self.user = []
        self.item = []
        self.rating = []
        self.rating_test = []
        self.new_items = []
        self.new_users = []
        self.new_ratings = []
        self.new_ratings_test = []
        self.links = []
        self.update = update

        self.unum_clusters = 6
        self.inum_clusters = 3

        self.modernUser_ratings = {}
        self.user_ratings = {}

        #self.db_store = MovieLensStore()


        self.logger = logging.getLogger('gunicorn.error')
        #current_app.logger.info('Testing current logger...')
        if not MovieLensStore.instance_init:
            self.dataset = Dataset()
            self.dataset.load_users("flaskr/data/u.user", self.user)
            self.dataset.load_items("flaskr/data/u.item", self.item)
            self.dataset.load_new_items("flaskr/new_data/ml-latest-small/items.data", self.new_items)
            self.dataset.load_new_users("flaskr/new_data/ml-latest-small/ratings.csv", self.new_users)
            self.dataset.load_ratings("flaskr/data/u.base", self.rating)
            self.dataset.load_ratings("flaskr/data/u.test", self.rating_test)
            self.dataset.load_ratings("flaskr/new_data/ml-latest-small/train.csv", self.new_ratings)
            self.dataset.load_ratings("flaskr/new_data/ml-latest-small/test.csv", self.new_ratings_test)
            self.dataset.load_links("flaskr/new_data/ml-latest-small/links.csv", self.links)


        self.item_data = pd.read_csv("flaskr/data/u.item", sep="|", encoding="latin-1", header=None)
        self.user_data = pd.read_csv("flaskr/data/u.user", sep="|", encoding="latin-1", header=None)
        self.rating_data = pd.read_csv("flaskr/data/u.base", sep='\t', encoding="latin-1", header=None)
        self.test_data = pd.read_csv("flaskr/data/u.test", sep='\t', encoding="latin-1", header=None)
        self.new_rating_data = pd.read_csv("flaskr/new_data/ml-latest-small/ratings.csv", sep=",", encoding="latin-1", header=None)
        self.new_item_data = pd.read_csv("flaskr/new_data/ml-latest-small/movies.csv", sep=",", encoding="latin-1")

        self.logger.info(f'{TAG}: Loaded raw data. Users Clusters={self.unum_clusters} and Item Clusters={self.inum_clusters}')


    def clutser_data(self):

        self.user_clusters, self.user_labels = cluster_users(self.user,self.user_data, self.unum_clusters)
        self.item_clusters, self.item_labels = cluster_items(self.item, self.item_data, self.inum_clusters)
        self.rating_clusters = cluster_ratings(self.item_labels, self.rating)


        self.modernItem_clusters, self.modernItem_labels = cluster_new_items(self.new_items, self.new_item_data, self.inum_clusters)
        self.modernRating_clusters = cluster_ratings(self.modernItem_labels, self.new_ratings)

        print("Clusterd users and items",)
        self.logger.info(f'{TAG}: Clustered users and items')

    def cluster_new_data(self):
        movielens_db = MovieLensStore.get_db()
        self.user_clusters, self.user_labels = cluster_users(movielens_db.get_all_users(),self.user_data, self.unum_clusters)
        self.item_clusters, self.item_labels = cluster_items(movielens_db.get_all_movies(), self.item_data, self.inum_clusters)
        self.rating_clusters = cluster_ratings(self.item_labels, movielens_db.get_all_ratings())


        self.modernItem_clusters, self.modernItem_labels = cluster_new_items(movielens_db.get_all_modern_movies(), self.new_item_data, self.inum_clusters)
        self.modernRating_clusters = cluster_ratings(self.modernItem_labels, movielens_db.get_all_modern_ratings())

        print("Clusterd users and items",)
        self.logger.info(f'{TAG}: Clustered users and items')      


    
    def fill_out_matrix(self):
        n_users = len(self.user)
        n_items = len(self.item)
        self.utility = np.zeros((n_users, n_items))
        for r in self.rating:
            self.utility[r.user_id-1][r.item_id-1] = r.rating


        # Finds the average rating for each user and stores it in the user's object
        for i in range(self.n_users):
            rated = np.nonzero(self.utility[i])
            n = len(rated[0])
            if n != 0:
                self.user[i].avg_r = np.mean(self.utility[i][rated])
            else:
                self.user[i].avg_r = 0.

    #TODO            
    def find_average_rating(self):
        pass
    
    def load_user_data(self):
        if self.update:
            self.logger.info(f'{TAG}: Using updated user data...')
            for u in self.new_users:
                self.modernUser_ratings[u.id] = []
                for r in self.new_ratings:
                    if u.id == r.user_id:
                        self.modernUser_ratings[u.id].append(r)

        else:
            for u in self.user:
                self.user_ratings[u.id] = []
                for r in self.rating:
                    if u.id == r.user_id:
                        self.user_ratings[u.id].append(r)

        print("User preprocessing done")
        self.logger.info(f'{TAG}: User preprocessing done')
    

    
    def pcs(self, x, y, curr):
        #x,y = users
        #All the items users x and y have rated.
        if curr:
            x_I = self.modernUser_ratings[x.id]
            y_I = self.modernUser_ratings[y.id]
        else:
            x_I = self.user_ratings[x.id]
            y_I = self.user_ratings[y.id]
        I_x = []
        I_y = []
        # All the items users x and y have both rated
        both = {}

        for r_x in x_I:
            both[r_x.item_id] = r_x
        
        for r_y in y_I:
            if r_y.item_id in both.keys():
                I_x.append(both[r_y.item_id])
                I_y.append(r_y)
        #print(I_x, I_y)
        #for r_x in x_I:
        #    for r_y in y_I:
        #        if r_x.item_id == r_y.item_id:
        #            I_x.append(r_x)
        #            I_y.append(r_y)
        if len(I_x) == 0: # If there are no common items users have rated, return 0
            return 0
        xAv = 0
        yAv = 0
        for (x,y) in itertools.zip_longest(x_I, y_I):
            if type(x) !=  type(None):
                xAv = xAv + x.rating
            if type(y) != type(None):
                yAv = yAv + y.rating
        xAv = xAv / len(x_I)
        yAv = yAv / len(y_I)
        #print ("xAv = " + str(xAv))
        #print ("yAv = " + str(yAv))
        num_sum = 0
        denom_sum = 0
        rxi_sum = 0
        ryi_sum = 0
        for (x,y) in itertools.zip_longest(I_x,I_y):
            num = (x.rating - xAv) * (y.rating - yAv)
            num_sum = num_sum + num
            rxi = (x.rating - xAv) * (x.rating - xAv)
            ryi = (y.rating - yAv) * (y.rating - yAv)
            rxi_sum = rxi_sum + rxi
            ryi_sum = ryi_sum + ryi

        
        #print(num_sum)
        denom_sum = math.sqrt(rxi_sum) * math.sqrt(ryi_sum)
        if denom_sum == 0:
            return 0
        else:
            #print ("num_sum = " + str(num_sum))
            #print ("denom_sum = " + str(denom_sum))
            #print(num_sum / denom_sum)
            return (num_sum / denom_sum)

    def new_pcs(self):
        pass


    # Guesses the ratings that user with id, user_id, might give to item with id, i_id.
    # We will consider the top_n similar users to do this.
    def guess(self,user_id, i_id, top_n):

        s_user = None
        for u in self.user:
            if user_id == u.id:
                s_user = u
                break
        
        #n most similar users to specified user(user_id)/
        #CLUSTER MOD: We are only going to consider users that share a cluster with the specified user.     
        score = {}
        u_cluster = self.user_labels[user_id]
        c_users = self.user_clusters[u_cluster]
        for u in c_users:
            if u.id != user_id:
                score[u.id] = self.pcs(s_user, u, False)
                
        top = sorted(score, key=score.__getitem__) 
        top = top[0:top_n]    

        #u_avg: average rating for all items for each of the n most similar users
        #CLUSTER MOD: Average rating for items that share a cluster with item_i
        u_avg = []
        i_cluster = self.item_labels[i_id]
        for u in top:
            if u in self.rating_clusters[i_cluster].keys():
                avg = self.rating_clusters[i_cluster][u]
                u_avg.append(avg)
            else:
                for us in self.user:
                    if us.id == u:
                        u_avg.append(us.avg_r)

        #print(u_avg)
        
        diff_u = []
        #diff_u list stores the difference of the rating for item_i from the average rating of all CLUSTER items for top_n similar users
        #0 in the diff_u list means that the user did not rate item i

        for (avg, u) in itertools.zip_longest(u_avg, top):
            match = False
            for r in self.user_ratings[u]:
                if i_id == r.item_id:
                    #print("Match found for user: " + str(u) + " and item: " + str(i_id))
                    diff = r.rating - avg
                    diff_u.append(diff)
                    match = True
            if match == False:
                diff_u.append(-1)
                    
        #print(diff_u)

        #avf_diff: is the average of the differences of the rating for item_i from the aerage rating of all items for top_n similar users who rated i
        avg_diff = 0
        count = 0 
        for num in diff_u:
            if num != -1:
                avg_diff = avg_diff + num
                count += 1
        
        if count != 0:
            avg_diff = avg_diff / count

        # the average rating of items for selected user
        su_avg = 0
        if user_id in self.rating_clusters[i_cluster].keys():
            su_avg = self.rating_clusters[i_cluster][user_id]
        else:
            su_avg = s_user.avg_r
    
        #print("avg_diff: " + str(avg_diff), "su_avg: " + str(su_avg))
        #add the average difference to the selected user average to selected user
        guess = su_avg + avg_diff

        #print("Guess: " + str(guess))

        return guess




    def updated_guess(self, user_id, i_id, top_n):   
        s_user = None
        for u in self.new_users:
            if user_id == u.id:
                s_user = u
                break
        #n most similar users to specified user(user_id)
        score = {}
        t0 = time.time()
        for u in self.new_users:
            if u.id != user_id:
                score[u.id] = self.pcs(s_user, u, True)
        t1 = time.time()
        x = t1- t0
        #print("PCS Scoring Time = " + str(x))
                
        top = sorted(score, key=score.__getitem__) 
        top = top[0:top_n]  

        #u_avg: average rating for all items for each of the n most similar users
        u_avg = []
        i_cluster = self.modernItem_labels[i_id]
        for u in top:
            #db function will be get_avg(i_cluster, u_id)
            if u in self.modernRating_clusters[i_cluster].keys():
                avg = self.modernRating_clusters[i_cluster][u]
                u_avg.append(avg)
            else:
                for us in self.user:
                    if us.id == u:
                        u_avg.append(us.avg_r)


        #diff_u list stores the difference of the rating for item_i from the average rating of all CLUSTER items for top_n similar users
        #0 in the diff_u list means that the user did not rate item i  
        diff_u = []

        for (avg, u) in itertools.zip_longest(u_avg, top):
            match = False
            for r in self.modernUser_ratings[u]:
                if i_id == r.item_id:
                    #print("Match found for user: " + str(u) + " and item: " + str(i_id))
                    diff = r.rating - avg
                    diff_u.append(diff)
                    match = True
            if match == False:
                diff_u.append(-1)
            
        #avf_diff: is the average of the differences of the rating for item_i from the aerage rating of all items for top_n similar users who rated i
        avg_diff = 0
        count = 0 
        for num in diff_u:
            if num != -1:
                avg_diff = avg_diff + num
                count += 1
        
        if count != 0:
            avg_diff = avg_diff / count

        # the average rating of items for selected user
        su_avg = 0
        if user_id in self.modernRating_clusters[i_cluster].keys():
            su_avg = self.modernRating_clusters[i_cluster][user_id]
        else:
            for r in self.modernUser_ratings[user_id]:
                su_avg += r.rating
            su_avg = su_avg/len(self.modernUser_ratings[user_id])



        guess = su_avg + avg_diff

        return guess
    
    def new_guess(self, user_id, i_id, top_n):
        movielens_db = MovieLensStore.get_db()
        s_user = self.db_store.get_modern_user(user_id)
    #n most similar users to specified user(user_id)
        score = {}
        t0 = time.time()
        for u in self.new_users:
            if u.id != user_id:
                score[u.id] = movielens_db.get_modern_user(u.id).pcs_score
        t1 = time.time()
        x = t1- t0
        #print("PCS Scoring Time = " + str(x))
                
        top = sorted(score, key=score.__getitem__) 
        top = top[0:top_n]  

    #u_avg: average rating for all items for each of the n most similar users
        u_avg = []
        i_cluster = movielens_db.get_modern_user(u).rating_clusters
        for u in top:
            if u in self.modernRating_clusters[i_cluster].keys():
                avg = self.modernRating_clusters[i_cluster][u]
                u_avg.append(avg)
            else:
                db_user = movielens_db.get_user(u)
                u_avg.append(db_user.avg_r)


    #diff_u list stores the difference of the rating for item_i from the average rating of all CLUSTER items for top_n similar users
    #0 in the diff_u list means that the user did not rate item i  
        diff_u = []

        for (avg, u) in itertools.zip_longest(u_avg, top):
            match = False
            user_ratings = movielens_db.get_modern_rating(user_id=u)
            for r in user_ratings:
                if i_id == r.item_id:
                    #print("Match found for user: " + str(u) + " and item: " + str(i_id))
                    diff = r.rating - avg
                    diff_u.append(diff)
                    match = True
            if match == False:
                diff_u.append(-1)
            
    #avf_diff: is the average of the differences of the rating for item_i from the aerage rating of all items for top_n similar users who rated i
        avg_diff = 0
        count = 0 
        for num in diff_u:
            if num != -1:
                avg_diff = avg_diff + num
                count += 1
        
        if count != 0:
            avg_diff = avg_diff / count

        # the average rating of items for selected user
        su_avg = 0
        if user_id in self.modernRating_clusters[i_cluster].keys():
            su_avg = self.modernRating_clusters[i_cluster][user_id]
        else:
            for r in movielens_db.get_modern_rating(user_id):
                su_avg += r.rating
            su_avg = su_avg/len(self.modernUser_ratings[user_id])



        guess = su_avg + avg_diff

        return guess

    
    def ml_run(self,top_n):

        predictions = []
        guesses = []
        test = []
        bar_length = len(self.rating_test)
        counter = 0
        bar = Bar('Processing', max = bar_length, suffix = '%(percent).1f%%')
        for r in self.rating_test:
            rating = round(self.guess(r.user_id, r.item_id, top_n), 5)
            row = [r.user_id, r.item_id, rating]
            guesses.append(rating)
            test.append(r.rating)
            predictions.append(row)
            bar.next()
            counter += 1

        bar.finish()
        print("Predictions Completed" + "\n", "User Clusters: " + str(self.unum_clusters) + "\n", "Item Clusters: " + str(self.inum_clusters) + "\n",  "Means Squared Error: " + str(mean_squared_error(guesses, test)))

        pred_csv = pd.DataFrame.from_records(predictions)
        pred_csv.to_csv(r'/Users/BEATFREAK/busyWork/ML_app/ml_backend/data/predictions.csv', index=False)

    
    def updated_mlRun(self,top_n):
        #.983 means sqaured error
        predictions = []
        guesses = []
        test = []
        bar_length = len(self.new_ratings_test)
        counter = 0
        bar = Bar('Processing', max = 1000, suffix = '%(percent).1f%%')
        for r in self.new_ratings_test:
            if counter == 1000:
                break
            rating = round(self.updated_guess(r.user_id, r.item_id, top_n), 5)
            row = [r.user_id, r.item_id, rating]
            guesses.append(rating)
            test.append(r.rating)
            predictions.append(row)
            bar.next()
            counter += 1

        bar.finish()
        print("Updated Predictions Completed" + "\n", "Item Clusters: " + str(self.inum_clusters) + "\n",  "Means Squared Error: " + str(mean_squared_error(guesses, test)))
        print(f'Top_N_Users: {top_n}')
        #pred_csv = pd.DataFrame.from_records(predictions)
        #pred_csv.to_csv(r'/Users/BEATFREAK/busyWork/ML_app/ml_backend/data/predictions.csv', index=False)









if __name__ == "__main__":
    engine = ReccEngine()
    engine.clutser_data()
    engine.load_user_data()

    engine.updated_mlRun(200)



## THINGS THAT YOU WILL NEED TO DO:
# Perform clustering on users and items
# Predict the ratings of the user-item pairs in rating_test
# Find mean-squared error


#Current Best:
    #Item Clusters: 5
    #TOP_N: 200
    #0.99520