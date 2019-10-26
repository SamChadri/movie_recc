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

update = True

if len(sys.argv) > 1 :
    if sys.argv[1] == "-u":
        update = False

# Store data in arrays
user = []
item = []
rating = []
rating_test = []
new_items = []
new_users = []
new_ratings = []
new_ratings_test = []
links = []

print(os.getcwd())
# Load the movie lens dataset into arrays
d = Dataset()
d.load_users("flaskr/data/u.user", user)
d.load_items("flaskr/data/u.item", item)
d.load_new_items("flaskr/new_data/ml-latest-small/items.data", new_items)
d.load_new_users("flaskr/new_data/ml-latest-small/ratings.csv", new_users)
d.load_ratings("flaskr/data/u.base", rating)
d.load_ratings("flaskr/data/u.test", rating_test)
d.load_ratings("flaskr/new_data/ml-latest-small/train.csv", new_ratings)
d.load_ratings("flaskr/new_data/ml-latest-small/test.csv", new_ratings_test)
d.load_links("flaskr/new_data/ml-latest-small/links.csv", links)

n_users = len(user)
n_items = len(item)

n_modernUsers = len(new_users)
n_modernItems = len(new_items) 

# Load raw data
item_data = pd.read_csv("flaskr/data/u.item", sep="|", encoding="latin-1", header=None)
user_data = pd.read_csv("flaskr/data/u.user", sep="|", encoding="latin-1", header=None)
rating_data = pd.read_csv("flaskr/data/u.base", sep='\t', encoding="latin-1", header=None)
test_data = pd.read_csv("flaskr/data/u.test", sep='\t', encoding="latin-1", header=None)
new_rating_data = pd.read_csv("flaskr/new_data/ml-latest-small/ratings.csv", sep=",", encoding="latin-1", header=None)
new_item_data = pd.read_csv("flaskr/new_data/ml-latest-small/movies.csv", sep=",", encoding="latin-1")


# Load cluster data
# optimal: 6,3
unum_clusters = 6
inum_clusters = 3

user_clusters, user_labels = cluster_users(user,user_data, unum_clusters)
item_clusters, item_labels = cluster_items(item, item_data, inum_clusters)
rating_clusters = cluster_ratings(item_labels, rating)


modernItem_clusters, modernItem_labels = cluster_new_items(new_items, new_item_data, inum_clusters)
modernRating_clusters = cluster_ratings(modernItem_labels, new_ratings)

print("Clusterd users and items", "Filling out utility matrix...")
# The utility matrix stores the rating for each user-item pair in the matrix form.
# Note that the movielens data is indexed starting from 1 (instead of 0).
utility = np.zeros((n_users, n_items))
for r in rating:
    utility[r.user_id-1][r.item_id-1] = r.rating


# Finds the average rating for each user and stores it in the user's object
for i in range(n_users):
    rated = np.nonzero(utility[i])
    n = len(rated[0])
    if n != 0:
        user[i].avg_r = np.mean(utility[i][rated])
    else:
        user[i].avg_r = 0.

# Stores all ratings for particular user in dictionary 
modernUser_ratings = {}
user_ratings = {}
if update:
    print("Using updated user data...")
    for u in new_users:
        modernUser_ratings[u.id] = []
        for r in new_ratings:
            if u.id == r.user_id:
                modernUser_ratings[u.id].append(r)

else:
    for u in user:
        user_ratings[u.id] = []
        for r in rating:
            if u.id == r.user_id:
                user_ratings[u.id].append(r)

print("User preprocessing done")


# Finds the Pearson Correlation Similarity Measure between two users
def pcs(x, y, curr):

    #x,y = users
    #All the items users x and y have rated.
    if curr:
        x_I = modernUser_ratings[x.id]
        y_I = modernUser_ratings[y.id]
    else:
        x_I = user_ratings[x.id]
        y_I = user_ratings[y.id]
    I_x = []
    I_y = []
    # All the items users x and y have both rated
    both = {}

    for r_x in x_I:
        both[r_x.item_id] = 1
    
    for r_y in y_I:
        if r_y.item_id in both.keys():
            I_x.append(r_x)
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
    """
    Insert your code here.
    """

# Guesses the ratings that user with id, user_id, might give to item with id, i_id.
# We will consider the top_n similar users to do this.
def guess(user_id, i_id, top_n):

    s_user = None
    for u in user:
        if user_id == u.id:
            s_user = u
            break
    
#n most similar users to specified user(user_id)/
#CLUSTER MOD: We are only going to consider users that share a cluster with the specified user.     
    score = {}
    u_cluster = user_labels[user_id]
    c_users = user_clusters[u_cluster]
    for u in c_users:
        if u.id != user_id:
            score[u.id] = pcs(s_user, u, False)
            
    top = sorted(score, key=score.__getitem__) 
    top = top[0:top_n]    

#u_avg: average rating for all items for each of the n most similar users
#CLUSTER MOD: Average rating for items that share a cluster with item_i
    u_avg = []
    i_cluster = item_labels[i_id]
    for u in top:
        if u in rating_clusters[i_cluster].keys():
            avg = rating_clusters[i_cluster][u]
            u_avg.append(avg)
        else:
            for us in user:
                if us.id == u:
                    u_avg.append(us.avg_r)

    #print(u_avg)
    
    diff_u = []
#diff_u list stores the difference of the rating for item_i from the average rating of all CLUSTER items for top_n similar users
#0 in the diff_u list means that the user did not rate item i

    for (avg, u) in itertools.zip_longest(u_avg, top):
        match = False
        for r in user_ratings[u]:
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
    if user_id in rating_clusters[i_cluster].keys():
        su_avg = rating_clusters[i_cluster][user_id]
    else:
        su_avg = s_user.avg_r
 
    #print("avg_diff: " + str(avg_diff), "su_avg: " + str(su_avg))
    #add the average difference to the selected user average to selected user
    guess = su_avg + avg_diff

    #print("Guess: " + str(guess))

    return guess


def updated_guess(user_id, i_id, top_n):
  
    s_user = None
    for u in new_users:
        if user_id == u.id:
            s_user = u
            break
#n most similar users to specified user(user_id)
    score = {}
    t0 = time.time()
    for u in new_users:
        if u.id != user_id:
            score[u.id] = pcs(s_user, u, True)
    t1 = time.time()
    x = t1- t0
    #print("PCS Scoring Time = " + str(x))
            
    top = sorted(score, key=score.__getitem__) 
    top = top[0:top_n]  

#u_avg: average rating for all items for each of the n most similar users
    u_avg = []
    i_cluster = modernItem_labels[i_id]
    for u in top:
        if u in modernRating_clusters[i_cluster].keys():
            avg = modernRating_clusters[i_cluster][u]
            u_avg.append(avg)
        else:
            for us in user:
                if us.id == u:
                    u_avg.append(us.avg_r)


#diff_u list stores the difference of the rating for item_i from the average rating of all CLUSTER items for top_n similar users
#0 in the diff_u list means that the user did not rate item i  
    diff_u = []

    for (avg, u) in itertools.zip_longest(u_avg, top):
        match = False
        for r in modernUser_ratings[u]:
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
    if user_id in modernRating_clusters[i_cluster].keys():
        su_avg = modernRating_clusters[i_cluster][user_id]
    else:
        for r in modernUser_ratings[user_id]:
            su_avg += r.rating
        su_avg = su_avg/len(modernUser_ratings[user_id])



    guess = su_avg + avg_diff

    return guess




def ml_run(top_n):

    predictions = []
    guesses = []
    test = []
    bar_length = len(rating_test)
    counter = 0
    bar = Bar('Processing', max = bar_length, suffix = '%(percent).1f%%')
    for r in rating_test:
        rating = round(guess(r.user_id, r.item_id, top_n), 5)
        row = [r.user_id, r.item_id, rating]
        guesses.append(rating)
        test.append(r.rating)
        predictions.append(row)
        bar.next()
        counter += 1

    bar.finish()
    print("Predictions Completed" + "\n", "User Clusters: " + str(unum_clusters) + "\n", "Item Clusters: " + str(inum_clusters) + "\n",  "Means Squared Error: " + str(mean_squared_error(guesses, test)))

    pred_csv = pd.DataFrame.from_records(predictions)
    pred_csv.to_csv(r'/Users/BEATFREAK/busyWork/ML_app/ml_backend/data/predictions.csv', index=False)


def updated_mlRun(top_n):
    #.983 means sqaured error
    predictions = []
    guesses = []
    test = []
    bar_length = len(new_ratings_test)
    counter = 0
    bar = Bar('Processing', max = bar_length, suffix = '%(percent).1f%%')
    for r in new_ratings_test:
        #if counter == 1000:
        #    break
        rating = round(updated_guess(r.user_id, r.item_id, top_n), 5)
        row = [r.user_id, r.item_id, rating]
        guesses.append(rating)
        test.append(r.rating)
        predictions.append(row)
        bar.next()
        counter += 1

    bar.finish()
    print("Updated Predictions Completed" + "\n", "Item Clusters: " + str(inum_clusters) + "\n",  "Means Squared Error: " + str(mean_squared_error(guesses, test)))

    pred_csv = pd.DataFrame.from_records(predictions)
    pred_csv.to_csv(r'/Users/BEATFREAK/busyWork/ML_app/ml_backend/data/predictions.csv', index=False)



if __name__ == "__main__":
    updated_mlRun(150)



## THINGS THAT YOU WILL NEED TO DO:
# Perform clustering on users and items
# Predict the ratings of the user-item pairs in rating_test
# Find mean-squared error
