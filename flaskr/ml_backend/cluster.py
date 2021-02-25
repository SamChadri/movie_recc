import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
from sklearn import preprocessing
from .movielens import *
import itertools


random = 123456789

def cluster_users(users, user_data, cluster_number):
    le = preprocessing.LabelEncoder()

    user_data[2] = le.fit_transform(user_data[2])
    user_data[3] = le.fit_transform(user_data[3])
    user_data[4] = le.fit_transform(user_data[4])

    X =  user_data.values

    kmeans_x = KMeans(n_clusters=cluster_number, random_state=0).fit(X) #prev 7- 1.076 prev 8- 1.083

    user_labels = {}
    user_clusters= {}
    for(cluster, user) in itertools.zip_longest(kmeans_x.labels_, users):
        user_labels[user.id] = cluster.item()
        if cluster not in user_clusters.keys():
            user_clusters[cluster.item()] = []
        user_clusters[cluster.item()].append(user)
    
    return user_clusters, user_labels

def cluster_items(items, item_data, cluster_number):

    item_data = item_data.drop([1,2,3,4], axis=1)

    X = item_data.values
    
    kmeans_x = KMeans(n_clusters=cluster_number, random_state=0).fit(X)#prev = 5 ... 1.085, 4 ... 1.076 18 ... 1.112. 2 is the winner for now
    
    item_labels = {}
    item_clusters = {}
    for (cluster, item) in itertools.zip_longest(kmeans_x.labels_, items):
        item_labels[item.id] = cluster.item()
        if cluster not in item_clusters.keys():
            item_clusters[cluster.item()] = []
        item_clusters[cluster.item()].append(item)

    return item_clusters, item_labels

def cluster_new_items(items, item_data, cluster_number):
    le = preprocessing.LabelEncoder()
    item_data["genres"] = le.fit_transform(item_data["genres"])
    item_data = item_data.drop(["title"], axis=1)

    X = item_data.values

    kmeans_x = KMeans(n_clusters=cluster_number, random_state=0).fit(X)

    item_labels = {}
    item_clusters = {}
    count = 0
    for (cluster, item) in itertools.zip_longest(kmeans_x.labels_, items):
        if type(item)  == type(None):
            print(count)
        count += 1
        item_labels[item.id] = cluster.item()
        if cluster not in item_clusters.keys():
            item_clusters[cluster.item()] = []
        item_clusters[cluster.item()].append(item)

    return item_clusters, item_labels

"""" Average user rating, stored in item clusters. """
def cluster_ratings(item_clusters, ratings):
    rating_clusters= {}
    for r in ratings:
        cluster_id = item_clusters[r.item_id]
        if cluster_id not in rating_clusters.keys():
            rating_clusters[cluster_id] = {}
        if r.user_id not in rating_clusters[cluster_id].keys():
            rating_clusters[cluster_id][r.user_id] = []
        rating_clusters[cluster_id][r.user_id].append(r)


    for key, value in rating_clusters.items():
        for key1, value1 in rating_clusters[key].items():
            avg = 0
            for r in value1:
                avg += r.rating
            avg = avg/len(value1)
            rating_clusters[key][key1] = avg

    return rating_clusters


