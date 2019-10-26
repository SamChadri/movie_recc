import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
from sklearn import preprocessing
from movielens import *
import itertools



def cluster_users(users, user_data):
    le = preprocessing.LabelEncoder()

    user_data[2] = le.fit_transform(user_data[2])
    user_data[3] = le.fit_transform(user_data[3])
    user_data[4] = le.fit_transform(user_data[4])

    X =  user_data.values

    kmeans_x = KMeans(n_clusters=30, random_state=0).fit(X)

    user_labels = {}
    user_clusters= {}
    for(cluster, user) in itertools.zip_longest(kmeans_x.labels_, users):
        user_labels[user.id] = cluster
        if cluster not in user_clusters.keys():
            user_clusters[cluster] = []
        user_clusters[cluster].append(user)
    
    return user_clusters, user_labels

def cluster_items(items, item_data):

    item_data = item_data.drop([1,2,3,4], axis=1)

    X = items.values

    kmeans_x = KMeans(n_clusters=50, random_state=0).fit(X)

    item_labels = {}
    item_clusters = {}
    for (cluster, item) in itertools.zip_longest(kmeans_x.labels_, items):
        item_labels[item.id] = cluster
        if cluster not in item_clusters.keys():
            item_clusters[cluster] = []
        item_clusters[cluster].append(item)

    return item_clusters, item_labels

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

