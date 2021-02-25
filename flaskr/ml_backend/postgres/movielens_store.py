from multiprocessing.queues import Queue
import re
import psycopg2
from kubernetes import client, config
import kubernetes
from kubernetes.client.rest import ApiException
import logging
import os
import json
from dateparser import parse
from datetime import datetime
from ..movielens import User,ModernUser,Rating,Item,ModernItem,Link, Dataset
from flaskr.ml_backend.cluster import *
from pprint import pprint
import itertools
import math
import pandas as pd
import json
from flask import current_app
from concurrent.futures import *
from multiprocessing import Pool, Queue
#from psycopg2.errors import SyntaxError
import multiprocessing as mp
from .db_worker import DBWorker
from tqdm import tqdm
import io
import random

import gevent.monkey
#gevent.monkey.patch_socket()
import psycogreen.gevent
#psycogreen.gevent.patch_psycopg()

import sys
TAG = 'MovieLensStore'

class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''
    def __init__(self,logger,level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO
    def write(self,buf):
        self.buf = buf.strip('\r\n\t ')
    def flush(self):
        self.logger.log(self.level, self.buf)


class TqdmStream(object):
  @classmethod
  def write(_, msg):
    tqdm.tqdm.write(msg, end='')



class MovieLensStore:
    event_queue = Queue(maxsize=943)

    @classmethod
    def init_db(cls):
        cls.__movielens_db = MovieLensStore()
        cls.__queue_init = False
        cls.__instance_init = True
    

    @classmethod
    def get_db(cls):
        return cls.__movielens_db

    @classmethod
    def instance_init(cls):
        return cls.__instance_init





    def __init__(self, key_file='flaskr/ml_backend/postgres/postgres-config.json'):
        #logging.basicConfig(level=logging.INFO, stream=TqdmStream)
        self.logger = logging.getLogger('gunicorn.error')
        #self.tqdm_out = TqdmToLogger(self.logger, level=logging.INFO) 
        config.load_incluster_config()
        v1_api = client.CoreV1Api()
        results = v1_api.list_service_for_all_namespaces(watch=False)
    
        for item in results.items:
            if item.metadata.name == 'postgres-service':
                self.postgres_ip = item.spec.cluster_ip
                self.postgres_port = item.spec.ports[0].port
                self.logger.info(f'{TAG}: Postgres Service Cluster IP: {item.spec.cluster_ip}, Port: {self.postgres_port}')

        with open(key_file) as f:
            data = json.load(f)
            self.__database = data['database']
            self.__user = data['user']
            self.__password = data['password']

        self.__key_file = key_file
        self.conn = psycopg2.connect(
            host=self.postgres_ip,
            port=self.postgres_port,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )
        self.unum_clusters = 6
        self.inum_clusters = 3

        self.pcs_loaded = False
        self.modern_pcs_loaded = False

        self.logger.info(f'{TAG}: Successfully connected to PostgreSQL Database:{self.__database} on IP:{self.postgres_ip} and Port:{self.postgres_port}')
        #self.clear_db()
        #mp.set_start_method('spawn')
        self.dataset = Dataset()
        self.event_queue = Queue()
        connection_check, pid = self.check_db_connections()
        if connection_check == 1:
            self.logger.info(f'{TAG}:: Proceeding to initialize database with postgres connection PID - {pid}')
            self.create_tables()
        elif connection_check == -1:
            self.logger.info(f'{TAG}:: Other worker performing database initialization. Postgres connection PID - {pid} on standby')
        elif connection_check == 0:
            self.logger.info(f'{TAG}:: Single worker application database initilization.')
        else:
            self.logger.info(f'{TAG}:: Failed to initialize database due to error.')



    def create_tables(self):

        FUNC_TAG = 'create_tables()'
        commands = [
            """CREATE EXTENSION IF NOT EXISTS "uuid-ossp" """,
            """CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY NOT NULL,
                age INT,
                sex CHAR(1),
                occupation VARCHAR (100),
                zip_code INT,
                cluster_num INT,
                rating_clusters json,
                pcs json
            )""",

            """CREATE TABLE IF NOT EXISTS modern_users (
                user_id INT PRIMARY KEY NOT NULL,
                average_rating INT,
                rating_clusters json,
                pcs json
            )""",
            """CREATE TABLE IF NOT EXISTS items (
                item_id INT PRIMARY KEY NOT NULL,
                cluster_num INT,
                title VARCHAR (255),
                release_date DATE,
                imdb_url TEXT,
                unknown SMALLINT,
                action SMALLINT,
                adventure SMALLINT,
                animation SMALLINT,
                childrens SMALLINT,
                comedy SMALLINT,
                crime SMALLINT,
                documentary SMALLINT,
                drama SMALLINT,
                fantasy SMALLINT,
                film_noir SMALLINT,
                horror SMALLINT,
                musical SMALLINT,
                mystery SMALLINT,
                romance SMALLINT,
                sci_fi SMALLINT,
                thriller SMALLINT,
                war SMALLINT,
                western SMALLINT
            )""",
            """CREATE TABLE IF NOT EXISTS modern_items(
                item_id INT PRIMARY KEY NOT NULL,
                cluster_num INT,
                title VARCHAR (255),
                action SMALLINT,
                adventure SMALLINT,
                animation SMALLINT,
                childrens SMALLINT,
                comedy SMALLINT,
                crime SMALLINT,
                documentary SMALLINT,
                drama SMALLINT,
                fantasy SMALLINT,
                film_noir SMALLINT,
                horror SMALLINT,
                imax SMALLINT,
                musical SMALLINT,
                mystery SMALLINT,
                romance SMALLINT,
                sci_fi SMALLINT,
                thriller SMALLINT,
                war SMALLINT,
                western SMALLINT,
                no_genre SMALLINT
            ) """,
            """CREATE TABLE IF NOT EXISTS ratings(
                rating_id uuid DEFAULT uuid_generate_v4 (),
                user_id INT,
                FOREIGN KEY (user_id)
                    REFERENCES users (user_id),
                item_id INT,
                FOREIGN KEY (item_id)
                    REFERENCES items (item_id),
                rating SMALLINT,
                time DATE
            ) """,
            """CREATE TABLE IF NOT EXISTS modern_ratings(
                rating_id uuid DEFAULT uuid_generate_v4 (),
                user_id INT,
                FOREIGN KEY (user_id)
                    REFERENCES modern_users (user_id),
                item_id INT,
                FOREIGN KEY (item_id)
                    REFERENCES modern_items(item_id),
                rating SMALLINT,
                time DATE
            )""",
            """CREATE TABLE IF NOT EXISTS links(
                link_id uuid DEFAULT uuid_generate_v4 (),
                item_id INT,
                FOREIGN KEY (item_id)
                    REFERENCES modern_items(item_id),
                imdb_id INT,
                tmdb_id INT
            ) """
        ]

        try:
            self.init_database(commands)
            self.test_db_func()
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.error(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            return
        
        


    def init_database(self, create_commands):
        FUNC_TAG = 'init_database'
        db_info = self.get_db_info()
        if db_info == 0:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: No tables found. Initializing Database...')
            curr = self.conn.cursor()
            for command in create_commands:
                curr.execute(command)
            curr.close()
            self.conn.commit()

            self.logger.info(f'{TAG}::{FUNC_TAG}:: Succesfully created tables. Importing data into database...')
            users_count, user_affected= self.load_users()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: user count = {users_count}, user records affected = {user_affected}')

            modern_users_count, modern_users_affected = self.load_modern_users()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: modern_user count = {modern_users_count}, modern_user records affected = {modern_users_affected}')

            items_count, items_records_affected = self.load_items()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: items count = {items_count}, modern_items records affected = {items_records_affected}')

            modern_items_count, modern_items_affected =  self.load_modern_items()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: modern_items count = {modern_items_count}, modern_items records affected = {modern_items_affected}')
            
            ratings_count, ratings_records_affected = self.load_ratings()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: ratings count = {ratings_count}, modern_ratings records affected = {ratings_records_affected}')

            modern_ratings_count, modern_ratings_records_affected = self.load_modern_ratings()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: modern_ratings = {modern_ratings_count}, modern_ratings records affected = {modern_ratings_records_affected}')

            links_count, links_records_affected = self.load_links()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: links count = {links_count}, links records affected = {links_records_affected}')

            self.load_user_clusters()

            self.load_item_clusters()

            self.load_rating_clusters()

            self.load_modern_item_clusters()

            self.load_modern_rating_clusters()

            #self.load_user_pcs_data()

            #self.load_modern_user_pcs_data()


        else:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: {self.__database} already initialized.')

    def get_db_info(self):
        FUNC_TAG='get_db_info'
        db_commands = [
            """ SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog' AND
                    schemaname != 'information_schema' """,
            """ SELECT COUNT (*)
                FROM {}"""
        ]

        try:
            curr = self.conn.cursor()
            curr.execute(db_commands[0])
            results = curr.fetchall()
            self.table_names = [name[0] for name in results]
            #self.logger.info(f'{TAG}::{FUNC_TAG}:: Tables = {self.table_names}')
            for name in self.table_names:
                curr.execute(db_commands[1].format(name))
                row_count = curr.fetchone()
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Table: {name} |  Row Count: {row_count[0]}')

            curr.close()
            self.conn.commit()

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0

        else:
            return len(self.table_names)

    def get_key_file(self):
        return self.__key_file
    #TODO: If I really feel like it, optimize transfers

    def check_db_connections(self):
        FUNC_TAG = "check_db_connections"
        pid_command = """SELECT pg_backend_pid()"""
        activity_command = """SELECT pid, state FROM pg_stat_activity WHERE datname = 'reccEngineDb' and pid != %s;"""

        try:
            curr = self.conn.cursor()
            curr.execute(pid_command)
            pid = curr.fetchone()[0]
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Current postgres PID - {pid}')
            curr.execute(activity_command, [pid])
            results = curr.fetchall()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Connection results - {results}')
            if len(results) > 0:
                self.logger.warn(f'{TAG}::{FUNC_TAG}:: Found other postgresql connections')
                connection = results[0]
                if pid < connection[0]:
                    return 1, pid
                else:
                    return -1, pid
            else:
                self.logger.info(f'{TAG}::{FUNC_TAG}:: No other connections found.')
                return 0, pid
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.error(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            return -2, 'NA'
    def load_users(self,file="flaskr/data/u.user"):
        FUNC_TAG='load_users'
        count_command = """SELECT COUNT (*) FROM users"""
        insert_command = """INSERT INTO users(user_id, age, sex, occupation, zip_code)
                            VALUES({}, {}, '{}', '{}', {})
                            RETURNING 1"""
        
        curr = self.conn.cursor()
        rows_affected = 0
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading users...')
        for entry in entries:
            e = entry.split('|')
            if len(e) == 5:
                try:
                    e[4] = int(e[4])
                except ValueError as error:
                    self.logger.error(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}. Setting ZipCode to -1')
                    e[4] = -1
                
                insert_statement = insert_command.format(*e)
                curr.execute(insert_statement)
                rows_affected += curr.fetchone()[0]

        f.close()

            
        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()

        #Returning the rows affected 
        return after_count, rows_affected

        

    def load_items(self,file="flaskr/data/u.item"):
        FUNC_TAG = 'load_items'
        count_command = """SELECT COUNT (*) FROM items """
        insert_command = """INSERT INTO items(item_id, title, release_date, imdb_url, unknown,
                                action, adventure, animation, childrens, comedy, crime, documentary,
                                drama, fantasy, film_noir, horror, musical, mystery, romance, sci_fi,
                                thriller, war, western)
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING 1"""
        
        curr = self.conn.cursor()
        rows_affected = 0
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading items...')
        for entry in entries:
            e = entry.split('|', 24)
            if len(e) == 24:
                e[1] = e[1].replace("'", "")
                try:
                    e[2] = parse(e[2]).strftime("%Y-%m-%d")
                except AttributeError as error:
                    e[2] = None
                    self.logger.info(f'{TAG}::{FUNC_TAG}:: Date Parse Error:{e}')
                e.remove(e[3])
                insert_statement = insert_command.format(*e)
                curr.execute(insert_command, e)
                rows_affected += curr.fetchone()[0]

        f.close()

        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()

        self.loaded_items = True
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded items.')

        return after_count, rows_affected

    
    def load_ratings(self, file="flaskr/data/u.base"):
        FUNC_TAG = 'load_ratings'
        count_command = """SELECT COUNT (*) FROM ratings"""
        insert_command = """INSERT INTO ratings(user_id, item_id, rating, time)
                            VALUES({},{},{},'{}')
                            RETURNING 1, rating_id, rating"""
        
        curr = self.conn.cursor()
        rows_affected = 0
        f = open(file, "r")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading ratings...')
        for entry in entries:
            e = entry.split('\t', 4)
            if len(e) == 4:
                #TODO Add in logs for rating_id and rating
                e[3] = datetime.fromtimestamp(int(e[3])).strftime("%Y-%m-%d")
                insert_statement = insert_command.format(*e)
                curr.execute(insert_statement)
                rows_affected += curr.fetchone()[0]
        
        f.close()
        
        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded ratings')

        return after_count, rows_affected

    #TODO Add in option for average rating for user
    def load_modern_users(self, file="flaskr/new_data/ml-latest-small/ratings.csv"):
        FUNC_TAG = 'load_new_users'
        count_command = """SELECT COUNT (*) FROM modern_users"""
        insert_command = """INSERT INTO modern_users(user_id)
                            VALUES ({})
                            RETURNING 1"""

        curr = self.conn.cursor()
        rows_affected = 0
        users = {}
        f = open(file,"r")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading new users...')
        for entry in entries:
            e = entry.split(',', 4)
            if len(e) == 4 and e[0] not in users.keys():
                users[e[0]] = 1
                insert_statement = insert_command.format(e[0])
                curr.execute(insert_statement)
                rows_affected += curr.fetchone()[0]

        f.close()

        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded modern_users.')

        return after_count, rows_affected


    def load_modern_items(self, file="flaskr/new_data/ml-latest-small/items.data"):
        FUNC_TAG = 'load_new_items'
        count_command = """SELECT COUNT (*) FROM modern_items"""
        insert_command = """INSERT INTO modern_items(item_id, title, action, adventure, animation, childrens, comedy,
                                crime, documentary, drama, fantasy, film_noir, horror, imax, musical, mystery, romance,
                                sci_fi, thriller, war, western, no_genre)
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING 1"""
        
        curr = self.conn.cursor()
        rows_affected = 0
        genres = {"Action":0, "Adventure":0, "Animation":0, "Children":0, "Comedy":0, "Crime":0, "Documentary":0, "Drama":0, \
        "Fantasy":0, "Film-Noir":0, "Horror":0, "IMAX":0, "Musical":0, "Mystery":0, "Romance":0, "Sci-Fi":0, "Thriller":0, "War":0, "Western":0, "(no genres listed)":0
        }
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        count = 0
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Load new items...')
        for entry in entries:
            e = entry.split('\t', 3)
            if len(e) == 3:
                genre = e[2].split('|')
                for g in genre:
                    genres[g] = 1
                val = [f'{value}' for (key,value) in sorted(genres.items())]
                if e[0] != 'movieId':
                    #print(count)
                    e[1] = e[1].replace("'", "\'")
                    values = [e[0],e[1]] + val
                    try:
                        curr.execute(insert_command, values)
                        rows_affected += curr.fetchone()[0]
                    except (TypeError, SyntaxError) as error:
                        self.logger.error(f'{TAG}::{FUNC_TAG}:: Error Message: {error}')
                        self.logger.error(f'{TAG}::{FUNC_TAG}:: values = {values}, entries = {e}, val = {val}], genres={genres}')
                        break
                    #count += 1
        f.close()

        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded modern_items')

        return after_count, rows_affected

    
    def load_modern_ratings(self, file="flaskr/new_data/ml-latest-small/ratings.csv"):
        FUNC_TAG = 'load_new_ratings'
        count_command = """SELECT COUNT (*) FROM modern_ratings"""
        insert_command = """INSERT INTO modern_ratings(user_id, item_id, rating, time)
                            VALUES({}, {}, {}, '{}')
                            RETURNING 1, rating_id, rating """

        curr = self.conn.cursor()
        rows_affected = 0
        f = open(file, "r")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading modern ratings...')
        for entry in entries:
            e = entry.split(',', 4)
            if len(e) == 4:
                #TODO Add in logs for rating_id and rating
                e[3] = datetime.fromtimestamp(int(e[3])).strftime("%Y-%m-%d")
                insert_statement = insert_command.format(*e)
                curr.execute(insert_statement)
                rows_affected += curr.fetchone()[0]
        
        f.close()
        
        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded modern_ratings.')

        return after_count, rows_affected



    def load_links(self, file="flaskr/new_data/ml-latest-small/links.csv"):
        FUNC_TAG = 'load_links'
        count_command = """SELECT COUNT (*) FROM links """
        insert_command = """INSERT INTO links(item_id, imdb_id, tmdb_id)
                            VALUES({}, {}, {})
                            RETURNING 1, link_id"""

        curr = self.conn.cursor()
        rows_affected = 0
        f = open(file, "r")
        text = f.read()
        entries = re.split("\n+", text)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading links...')
        for entry in entries:
            e = entry.split(',', 3)
            if len(e) == 3 and e[0] != "movieId":
                if e[2] == '':
                    self.logger.info(f'{TAG}::{FUNC_TAG}:: Entry Values = {e}. Missing tmdb_id. Replacing with -1')
                    e[2] = -1
                curr.execute(insert_command.format(*e))
                rows_affected += curr.fetchone()[0]
                
        f.close()

        self.conn.commit()
        curr.execute(count_command)
        after_count = curr.fetchone()[0]
        curr.close()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded links')

        return after_count, rows_affected
    
    def load_user_clusters(self):
        FUNC_TAG = 'load_user_clusters'
        users = []
        self.dataset.load_users("flaskr/data/u.user", users)
        user_data = pd.read_csv("flaskr/data/u.user", sep="|", encoding="latin-1", header=None)

        user_clusters, user_labels = cluster_users(users, user_data, self.unum_clusters)
        update_command = """UPDATE users
                            SET cluster_num = %s
                            WHERE user_id = %s"""
        records_affected = 0
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading user clusters....')
        try:

            curr = self.conn.cursor()
            for key, value in user_labels.items():
                curr.execute(update_command, (value,key))
                records_affected += curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded user clusters. {records_affected} records affected.')      
            pass
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            self.conn.cursor().close()
            return 0
        
        return records_affected

    def load_item_clusters(self):
        FUNC_TAG = 'load_item_clusters'
        items = []
        self.dataset.load_items("flaskr/data/u.item",items)
        item_data = pd.read_csv("flaskr/data/u.item", sep="|", encoding="latin-1", header=None)

        _ , self.item_labels = cluster_items(items, item_data, self.inum_clusters)
        update_command = """UPDATE items
                            SET cluster_num = %s
                            WHERE item_id = %s"""
        records_affected = 0 
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading item clusters...')
        try:
            curr = self.conn.cursor()
            for key, value in self.item_labels.items():
                curr.execute(update_command, (value, key))
                records_affected += curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded item clusters. {records_affected} records affected.')
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            self.conn.cursor().close()
            return 0

        return records_affected

    def load_rating_clusters(self):
        FUNC_TAG = 'load_rating_clusters'
        ratings = []
        self.dataset.load_ratings("flaskr/data/u.base", ratings)
        
        rating_clusters = cluster_ratings(self.item_labels, ratings)

        update_command = """UPDATE users
                            SET rating_clusters = %s
                            WHERE user_id = %s"""
        
        records_affected = 0 
        user_list, _ = self.get_all_users()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading rating clusters...')
        try:
            curr = self.conn.cursor()
                    
            for user in user_list:
                user_rating_cluster = {}
                for item_cluster, ratings in rating_clusters.items():
                    if user in ratings.keys():
                        user_rating_cluster[item_cluster] = ratings[user]
                curr.execute(update_command, (json.dumps(user_rating_cluster),user))
                records_affected += curr.rowcount
            
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded rating clusters. {records_affected} records affected')
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()
            return 0

        return records_affected

    def load_modern_item_clusters(self):
        FUNC_TAG = 'load_modern_item_clusters'
        modern_items = []
        self.dataset.load_new_items("flaskr/new_data/ml-latest-small/items.data", modern_items)
        modern_item_data = pd.read_csv("flaskr/new_data/ml-latest-small/movies.csv", sep=",", encoding="latin-1")
        update_command = """UPDATE modern_items
                            SET cluster_num = %s
                            WHERE item_id = %s"""
        
        records_affected =  0
        _ , self.modernItem_labels = cluster_new_items(modern_items, modern_item_data, self.inum_clusters)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading modern item clusters...')
        try:
            curr = self.conn.cursor()
            for key, value in self.item_labels.items():
                curr.execute(update_command, (value, key))
                records_affected += curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded item clusters. {records_affected} records affected.')
        
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()
            return 0
        return records_affected

    def load_modern_rating_clusters(self):
        FUNC_TAG = 'load_modern_rating_clusters'
        modern_ratings = []
        self.dataset.load_ratings("flaskr/new_data/ml-latest-small/ratings.csv", modern_ratings)
        modern_rating_clusters = cluster_ratings(self.modernItem_labels, modern_ratings)
        self.logger.info(f'{TAG}{FUNC_TAG}:: Modern ratings in memory....')
        update_command = """UPDATE modern_users
                            SET rating_clusters = %s
                            WHERE user_id = %s"""

        records_affected = 0
        user_list, _ = self.get_all_modern_users()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Loading modern rating clusters...')
        try:
            curr = self.conn.cursor()
            for user in user_list:
                user_rating_cluster = {}
                for item_cluster, ratings in modern_rating_clusters.items():
                    if user in ratings.keys():
                        user_rating_cluster[item_cluster] = ratings[user]
                curr.execute(update_command, (json.dumps(user_rating_cluster), user))
                records_affected += curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Loaded user clusters. {records_affected} records affected')
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()
            return 0

        return records_affected


    def clear_db(self):
        FUNC_TAG = 'clear_db'
        delete_command = """DO $$ DECLARE
                                r RECORD;
                            BEGIN
                                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                                END LOOP;
                            END $$;"""

        
        curr = self.conn.cursor()

        curr.execute(delete_command)

        curr.close()
        self.conn.commit()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: {self.__database} tables cleared. ')
        return self.get_db_info()


    #TODO: Change items to movies
    def get_user(self, user_id):
        command = """SELECT * FROM users
                     WHERE user_id = %s"""

        curr = self.conn.cursor()
        curr.execute(command, [user_id])
        result = curr.fetchone()
        curr.close()
        self.conn.commit()
        user = User(result[0], result[1], result[2], result[3], result[4],cluster_num=result[5], rating_clusters=result[6], pcs_score=result[7])
        
        return user

    def get_all_users(self):
        FUNC_TAG = 'get_all_users'
        query = """SELECT user_id FROM users"""
        try:
            curr = self.conn.cursor()
            curr.execute(query)
            records_affected = curr.rowcount
            result = curr.fetchone()
            user_ids = []
            while result is not None:
                user_ids.append(result[0])
                result = curr.fetchone()
            
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: {records_affected} users queried.')
        
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            self.conn.cursor().close()
            return [], 0
        
        return user_ids, records_affected

    def insert_user(self, user):
        FUNC_TAG = 'insert_user'
        insert_command = """INSERT INTO users(user_id, age, sex, occupation, zip_code)
                            VALUES(%(id)s, %(age)s, %(sex)s, %(occupation)s, %(zip)s)
                            RETURNING 1, user_id"""
        
        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, user.__dict__)
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Movie inserted with id {user.id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0
        return records_affected

    def delete_user(self, user_id):
        FUNC_TAG = 'delete_user'
        delete_command = """DELETE FROM users
                          WHERE user_id = %s"""
        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [user_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Deleted user with id {user_id}.')

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0

        return rows_deleted
        

    def get_modern_user(self, user_id):
        command = """SELECT * FROM modern_users
                     WHERE user_id = %s"""
        
        curr = self.conn.cursor()
        curr.execute(command, [user_id])
        result = curr.fetchone()
        curr.close()
        self.conn.commit()
        modern_user = ModernUser(result[0],pcs_score=result[1], rating_clusters=result[2])

        return modern_user 

    def get_all_modern_users(self):
        FUNC_TAG = 'get_all_modern_users'
        query = """SELECT user_id FROM modern_users"""
        user_ids = []
        try:
            curr = self.conn.cursor()
            curr.execute(query)
            records_affected = curr.rowcount
            result = curr.fetchone()
            while result is not None:
                user_ids.append(result[0])
                result = curr.fetchone()
            
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: {records_affected} users queried.')
        
        except(Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            self.conn.cursor().close()
            
            return user_ids, 0
        
        return user_ids, records_affected
    #TODO Update to include average rating
    def insert_modern_user(self, modern_user: ModernUser):
        FUNC_TAG = 'insert_modern_user'
        insert_command = """INSERT INTO modern_users(user_id)
                            VALUES (%(id)s)
                            RETURNING 1"""

        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, modern_user.__dict__)
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Movie inserted with id {modern_user.id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0
        return records_affected

    def delete_modern_user(self, modern_user_id):
        FUNC_TAG = 'delete_modern_user'
        delete_command = """DELETE FROM modern_users
                            WHERE user_id = %s"""
        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [modern_user_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Deleted Modern user with id {modern_user_id}')

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0

        return rows_deleted


    def get_rating(self, user_id=None, rating_id=None, movie_id=None):
        user_query = """SELECT * FROM ratings
                        WHERE user_id = %s"""
        rating_query = """SELECT * FROM ratings
                        WHERE rating_id = %s"""
        movie_query = """SELECT * FROM ratings
                         WHERE item_id = %s"""
        
        FUNC_TAG = 'get_rating'
        try:
            curr = self.conn.cursor()

            if user_id != None:
                curr.execute(user_query, [user_id])
                results = curr.fetchall()
                modern_ratings = []
                for result in results:
                    modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
                
                curr.close()
                self.conn.commit()
                #self.logger.info(f'{TAG}::{FUNC_TAG}:: Retreived ratings for user = {user_id}. Results = {modern_ratings}')
                return modern_ratings
            elif movie_id != None:
                curr.execute(movie_query, [movie_id])
                results = curr.fetchall()
                modern_ratings = []
                for result in results:
                    modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
                
                curr.close()
                self.conn.commit()
                return modern_ratings
            elif rating_id != None:
                curr.execute(rating_query, [rating_id])
                result = curr.fetchone() 
                curr.close()
                self.conn.commit()
                return Rating(result[1], result[2], result[3], result[4], rating_id=result[0])
            
            else:
                return None
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()

    def get_all_ratings(self):
        FUNC_TAG = "get_all_ratings"
        rating_query = """SELECT * FROM modern_ratings"""

        try:
            curr = self.conn.cursor()
            curr.execute(rating_query)
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
            
            return modern_ratings
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return None
            

        


    def insert_rating(self, rating : Rating):
        FUNC_TAG = 'insert_rating'
        insert_command = """INSERT INTO ratings(user_id, item_id, rating, time)
                            VALUES(%(user_id)s,%(item_id)s,%(rating)s,%(time)s)
                            RETURNING 1, rating_id, rating"""

        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, rating.__dict__)
            rating_id = curr.fetchone()[1]
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Rating inserted with id {rating_id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0
        return rating_id

    def delete_rating(self, rating_id):
        FUNC_TAG = 'delete_rating'
        delete_command = """DELETE FROM ratings
                            WHERE rating_id = %s"""

        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [rating_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Rating with id {rating_id} deleted.')

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0

        return rows_deleted

    def get_modern_rating(self, user_id=None, rating_id=None, movie_id=None):
        user_query = """SELECT * FROM modern_ratings
                        WHERE user_id = %s"""
        rating_query = """SELECT * FROM modern_ratings
                        WHERE rating_id = %s"""
        movie_query = """SELECT * FROM modern_ratings
                         WHERE item_id = %s"""
        curr = self.conn.cursor()

        if user_id != None:
            curr.execute(user_query, [user_id])
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
            
            return modern_ratings
        elif movie_id != None:
            curr.execute(movie_query, [movie_id])
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
            
            return modern_ratings
        elif rating_id != None:
            curr.execute(rating_query, [rating_id])
            result = curr.fetchone() 
            return Rating(result[1], result[2], result[3], result[4], rating_id=result[0])

        else:
            return None

    def get_all_modern_ratings(self):
        FUNC_TAG = "get_all_modern_ratings"
        rating_query = """SELECT * FROM modern_ratings"""

        try:
            curr = self.conn.cursor()
            curr.execute(rating_query)
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(Rating(result[1], result[2], result[3], result[4], rating_id=result[0]))
            
            return modern_ratings
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return None
        
    def insert_modern_rating(self, modern_rating : Rating):
        FUNC_TAG = 'insert_modern_rating'
        insert_command = """INSERT INTO modern_ratings(user_id, item_id, rating, time)
                            VALUES(%(user_id)s, %(item_id)s, %(rating)s, %(time)s)
                            RETURNING 1, rating_id, rating"""

        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, modern_rating.__dict__)
            rating_id = curr.fetchone()[1]
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Movie inserted with id {rating_id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0
        return rating_id

    def delete_modern_rating(self, modern_rating_id):
        FUNC_TAG = 'delete_modern_rating'
        delete_command = """DELETE FROM modern_ratings
                           WHERE rating_id = %s"""
    
        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [modern_rating_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Modern Rating  with id {modern_rating_id} deleted')

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return 0

        return rows_deleted  
        


    def get_movie(self, movie_id):
        FUNC_TAG= 'get_movie'
        movie_command = """SELECT * FROM items
                           WHERE item_id = %s"""

        
     
        curr = self.conn.cursor()
        curr.execute(movie_command, [movie_id])
        result = curr.fetchone()
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Database result {result}')
        retval = Item(arg_list=result)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Item creation result: {retval}')
        curr.close()
        self.conn.commit()
        return retval

    def get_all_movies(self):
        FUNC_TAG = "get_all_movies"
        movie_query = """SELECT * FROM items"""

        try:
            curr = self.conn.cursor()
            curr.execute(movie_query)
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(Item(arg_list=result))
            return modern_ratings
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return None

    def insert_movie(self, movie: Item):
        FUNC_TAG = 'insert_movie'
        insert_command = """INSERT INTO items(item_id, title, release_date, imdb_url, unknown,
                                action, adventure, animation, childrens, comedy, crime, documentary,
                                drama, fantasy, film_noir, horror, musical, romance, sci_fi,
                                thriller, war, western)
                            VALUES(%(id)s, %(title)s, %(release_date)s, %(imdb_url)s, %(unknown)s, %(action)s, %(adventure)s, %(animation)s,
                                %(childrens)s, %(comedy)s, %(crime)s, %(documentary)s, %(drama)s, %(fantasy)s, %(film_noir)s, %(horror)s,
                                %(musical)s, %(romance)s, %(sci_fi)s, %(thriller)s, %(war)s, %(western)s)
                            RETURNING 1"""
        
        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, movie.__dict__)
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Movie inserted with id{movie.id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0
        return records_affected
    
    def delete_movie(self, movie_id):
        FUNC_TAG = 'delete_movie'
        insert_command = """DELETE FROM items
                            WHERE item_id = %s"""

        try:
            curr = self.conn.cursor()
            curr.execute(insert_command, [movie_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Movie deleted with id {movie_id}.')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0

        return rows_deleted        
        

    def get_modern_movie(self, movie_id):
        modern_movie_command = """SELECT * FROM modern_items
                                  WHERE item_id = %s"""
        
        curr = self.conn.cursor()
        curr.execute(modern_movie_command, [movie_id])
        result = curr.fetchone()
        curr.close()
        self.conn.commit()
        return ModernItem(arg_list=result)
    
    def get_all_modern_movies(self):
        FUNC_TAG = "get_all_modern_movies"
        movie_query = """SELECT * FROM modern_items"""

        try:
            curr = self.conn.cursor()
            curr.execute(movie_query)
            results = curr.fetchall()
            modern_ratings = []
            for result in results:
                modern_ratings.append(ModernItem(arg_list=result))
            return modern_ratings
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            self.conn.cursor().close()
            return None

    def insert_modern_movie(self, movie : ModernItem):
        insert_command = """INSERT INTO modern_items(item_id, title, action, adventure, animation, childrens, comedy,
                                crime, documentary, drama, fantasy, film_noir, horror, imax, musical, mystery, romance,
                                sci_fi, thriller, war, western, no_genre)
                            VALUES(%(id)s, %(title)s, %(action)s, %(adventure)s, %(animation)s, %(childrens)s, %(comedy)s, %(crime)s, %(documentary)s, %(drama)s,
                                    %(fantasy)s, %(film_noir)s, %(horror)s, %(imax)s, %(musical)s, %(mystery)s, %(romance)s, %(sci_fi)s, %(thriller)s, %(war)s, %(western)s, %(no_genre)s)
                            RETURNING 1"""
        
        curr = self.conn.cursor()
        curr.execute(insert_command, movie.__dict__)
        record_affected = curr.fetchone()
        curr.close()
        self.conn.commit()
        return record_affected

    def delete_modern_movie(self, movie_id):
        FUNC_TAG = 'delete_modern_movie'
        delete_command = """DELETE FROM modern_items
                            WHERE item_id = %s"""
        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [movie_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Modern Movie deleted with id {movie_id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0

        return rows_deleted



    def get_link(self, movie_id, link_id=None):
        link_command = """SELECT * FROM links
                          WHERE item_id = %s"""

        curr = self.conn.cursor()
        curr.execute(link_command, [movie_id])
        result = curr.fetchone()
        curr.close()
        self.conn.commit()
        return Link(result[1], result[2], result[3], link_id=result[0])

    def insert_link(self, link):
        FUNC_TAG = 'insert_link'
        link_command = """INSERT INTO links(item_id, imdb_id, tmdb_id)
                            VALUES(%(movie_id)s, %(imdb_id)s, %(tmdb_id)s)
                            RETURNING 1, link_id"""
        
        link_id = None

        try:
            curr = self.conn.cursor()
            curr.execute(link_command, link.__dict__)
            result = curr.fetchone()
            curr.close()
            self.conn.commit()
            link_id = result[1]
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Inserted link with id {link_id}')
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return link_id
        
        return link_id
    
    def delete_link(self, link_id):
        FUNC_TAG = 'delete_link'
        delete_command = """DELETE FROM links
                            WHERE link_id = %s"""
        rows_deleted = 0
        try:
            curr = self.conn.cursor()
            curr.execute(delete_command, [link_id])
            rows_deleted = curr.rowcount
            curr.close()
            self.conn.commit()
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Deleted link with id {link_id}')

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return 0

        return rows_deleted
        
    
    def db_pcs(self, first_user, second_user, curr):
        #x,y = users
        #All the items users x and y have rated.
        FUNC_TAG = 'db_pcs'
        #self.logger.info(f'{TAG}::{FUNC_TAG}:: Calculating pcs with user 1 = {first_user} and user 2 =  {second_user}.')
        if curr:
            x_I = self.get_modern_rating(first_user)
            y_I = self.get_modern_rating(second_user)
        else:
            x_I = self.get_rating(first_user)
            y_I = self.get_rating(second_user)

        #self.logger.info(f'{TAG}::{FUNC_TAG}:: User 1 ratings = {x_I}, User 2 ratings = {y_I}')


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
    @staticmethod
    def load_user_pcs_data(user_list, postgres_ip, postgres_port, event_queue, processes=2, key_file='flaskr/ml_backend/postgres/postgres-config.json'):
        FUNC_TAG = 'load_user_pcs_data'
        update_command = """UPDATE users
                            SET pcs = %s
                            WHERE user_id = %s"""


        pcs = {}
        records_affected = 0
        logger = logging.getLogger('gunicorn.error')   
        logger.info(f'{TAG}::{FUNC_TAG}:: Loading user pcs data....')
        #pg_bar = tqdm(total=len(user_list), file=tqdm_out)
        worker = DBWorker(key_file, postgres_ip, postgres_port, user_list)
        progress_step = 0
        chunksize= 1
        try:
            progress_data = {}
            progress_data['processes'] = processes
            progress_data['chunksize'] = chunksize
            progress_data['total_size'] = len(user_list)
            logger.info(f'{TAG}::{FUNC_TAG}:: Creating {processes} to process {len(user_list)} users. Chunksize = {chunksize}.')
            with mp.Pool(processes=processes) as pool:
                logger.info(f'{TAG}::{FUNC_TAG}:: Running workers to process pcs data....')
                for user in pool.imap(worker.update_pcs, user_list, chunksize=chunksize):
                    records_affected += 1
                    progress_data['curr_user'] = user
                    progress_data['records_affected'] = records_affected
                    data = f'data: {json.dumps(progress_data)}\n\n'
                    logger.info(f'{TAG}::{FUNC_TAG}:: Finished processing user =  {user}. Records affected = {records_affected}.')
                    event_queue.put_nowait(data)
            logger.info(f'{TAG}::{FUNC_TAG}:: Inserted PCS data. {records_affected} records affected.')
        except (Exception, psycopg2.DatabaseError) as error:
            logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            error = {'error': error}
            data = f'data: {json.dumps(error)}\n\n'
            event_queue.put_nowait(data)
            #yield json.dumps({'data': error})


    @staticmethod
    def load_modern_user_pcs_data(user_list, postgres_ip, postgres_port, event_queue, processes=2, key_file='flaskr/ml_backend/postgres/postgres-config.json'):
        FUNC_TAG = 'load_user_pcs_data'
        update_command = """UPDATE modern_users
                            SET pcs = %s
                            WHERE user_id = %s"""

        pcs = {}
        records_affected = 0
        logger = logging.getLogger('gunicorn.error')
        logger.info(f'{TAG}::{FUNC_TAG}:: Loading modern user pcs data....')
        #pg_bar = tqdm(total=len(user_list), file=tqdm_out)
        worker = DBWorker(key_file, postgres_ip, postgres_port, user_list)
        chunksize= 1
        
        try:
            progress_data = {}
            progress_data['processes'] = processes
            progress_data['chunksize'] = chunksize
            progress_data['total_size'] = len(user_list)
            logger.info(f'{TAG}::{FUNC_TAG}:: Creating {processes} to process {len(user_list)} modern_users. Chunksize = {chunksize}.')
            with mp.get_context('spawn').Pool(processes=processes) as pool:
                logger.info(f'{TAG}::{FUNC_TAG}:: Running workers to process modern pcs data....')
                for user in pool.imap(worker.update_modern_pcs, user_list, chunksize=chunksize):
                    records_affected += 1
                    progress_data['curr_user'] = user
                    progress_data['records_affected'] = records_affected
                    data = f'data: {json.dumps(progress_data)}\n\n'
                    logger.info(f'{TAG}::{FUNC_TAG}:: Finished processing user =  {user}. Records affected = {records_affected}.')
                    event_queue.put_nowait(data)
            logger.info(f'{TAG}::{FUNC_TAG}:: Inserted PCS data. {records_affected} records affected.')
        except (Exception, psycopg2.DatabaseError) as error:
            logger.info(f'{TAG}::{FUNC_TAG}:: Error occured: {error}')
            error = {'error': error}
            data = f'data: {json.dumps(error)}\n\n'
            event_queue.put_nowait(data)
            #yield json.dumps({'data': error}) + '\n\n'

            
        

    
    def test_db_func(self):
        FUNC_TAG = 'test_db_func'
        user_id = 10
        movie_id = 10
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_user() with user_id = {user_id}')
        user = self.get_user(user_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {user}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_modern_user() with user_id = {user_id}')
        user = self.get_modern_user(user_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {user}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_rating() with user_id = {user_id}')
        ratings = self.get_rating(user_id=user_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result length = {len(ratings)}')
        #for item in ratings:
        #    self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {item}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_rating() with movie_id = {movie_id}')
        ratings = self.get_rating(movie_id=movie_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result length = {len(ratings)}')
        #for item in ratings:
        #    self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {item}')

        rating_id = ratings[0].rating_id

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_rating() with rating_id = {rating_id}')
        rating = self.get_rating(rating_id=rating_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {rating}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_modern_rating() with user_id = {user_id}')
        ratings = self.get_modern_rating(user_id=user_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result length = {len(ratings)}')
        #for item in ratings:
            #self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {item}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_modern_rating() with movie_id = {movie_id}')
        ratings = self.get_modern_rating(movie_id=movie_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result length = {len(ratings)}')
        #for item in ratings:
            #self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {item}')
        
        rating_id = ratings[0].rating_id

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_modern_rating() with rating_id = {rating_id}')
        rating : Rating = self.get_modern_rating(rating_id=rating_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {rating}')


        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_movie() with movie_id = {movie_id}')
        movie : Item = self.get_movie(movie_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {movie}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_modern_movie() with movie_id = {movie_id}')
        modern_movie = self.get_modern_movie(movie_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {modern_movie}')

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing get_link() with movie_id = {movie_id}')
        link = self.get_link(movie_id=movie_id)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Result = \n {link}')

        test_id = random.randint(1000,2000)
        test_user = User(test_id, 23, 'M', 'Software Engineer', 6969)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_user()')
        records_affected = self.insert_user(test_user)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_user()')
        self.delete_user(test_user.id)

        test_id = random.randint(1000,2000)
        test_modern_user = ModernUser(test_id)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_modern_user()')
        self.insert_modern_user(test_modern_user)
        
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_modern_user()')
        self.delete_modern_user(test_modern_user.id)

        date = datetime.fromtimestamp(885921316).strftime("%Y-%m-%d")
        test_rating = Rating(10, 10, 6.69, date)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_rating()')
        rating_id = self.insert_rating(test_rating)
        
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_rating()')
        self.delete_rating(rating_id)



        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_modern_rating()')
        self.insert_modern_rating(rating)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete modern_rating()')
        self.delete_modern_rating(rating_id)

        
        movie.id = random.randint(-3000,-1000)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_movie()')
        self.insert_movie(movie)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_movie()')
        self.delete_movie(movie.id)


        modern_movie.id = random.randint(-3000,-1000)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_modern_movie()')
        self.insert_modern_movie(modern_movie)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_modern_movie')
        self.delete_modern_movie(modern_movie.id)

        test_link = Link(10, 696969,96969)
        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing insert_link()')
        link_id = self.insert_link(test_link)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Testing delete_link()')
        self.delete_link(link_id)

        self.logger.info(f'{TAG}::{FUNC_TAG}:: Passed all tests. Database ready to use.')




        
    
        


        


    
