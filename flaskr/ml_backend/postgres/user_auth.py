from concurrent.futures import *
from enum import Enum
from multiprocessing import Pool, Queue
#from psycopg2.errors import SyntaxError
import multiprocessing as mp
from .db_worker import DBWorker
from tqdm import tqdm
import io
import sys
import json
import psycopg2
from kubernetes import client, config
import logging

TAG = 'MovieLensStore'


class UserCredential:

    def __init__(self, user_key, email):
        self.user_key = user_key
        self.email = email


    
    def set_userId(self, user_id):
        self.user_id = user_id


class UserAuthStore:

    USER_KEY: int = 0
    EMAIL: int = 1

    @classmethod
    def init_auth_store(cls):
        cls.__auth_store = UserAuthStore()
    
    @classmethod
    def get_auth_store(cls):
        return cls.__auth_store
        

    def __init__(self, key_file='flaskr/ml_backend/postgres/postgres-config.json'):
        self.logger = logging.getLogger('gunicorn.error')
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

        self.init_tables()

    
    def init_tables(self):
        FUNC_TAG = "init_tables()"

        commands = [
            """CREATE EXTENSION IF NOT EXISTS "uuid-ossp" """,
            """CREATE TABLE IF NOT EXISTS user_creds (
                user_key uuid DEFAULT uuid_generate_v4 () PRIMARY KEY NOT NULL,
                email TEXT,
                password TEXT
            )""",
        ]

        try:
            self.get_cred_info()
            if self.get_cred_info() == 0:
                curr = self.conn.cursor()
                for command in commands:
                    curr.execute(command)
                curr.close()
                self.conn.close()
            
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
    
    


    
    def get_cred_info(self):
        FUNC_TAG = "get_cred_info"

        db_commands = [
            """ SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog' AND
                    schemaname != 'information_schema'
                    tablename = user_creds """,
            
            """ SELECT COUNT (*)
                FROM user_creds""",

        ]


        try:
            curr = self.conn.cursor()
            curr.execute(db_commands[0])
            results = curr.fetchall()
            if len(results) != 0:
                curr.execute(db_commands[1])
                row_count = curr.fetchone()
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Table: user_creds |  Row Count: {row_count[0]}')
                curr.commit()
                self.conn.close()
                return row_count
            else:
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Table user_creds does not exist. Initializing database...')
                curr.commit()
                self.conn.close()
                return 0

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return -1

    
    def get_user(self, identifier: str, type: int):
        FUNC_TAG = "get_user"
        if type == UserAuthStore.USER_KEY:
            command = """SELECT email FROM user_creds
                         WHERE user_key = %s"""
            
            try:
                curr = self.conn.cursor()
                curr.execute(command, [identifier])
                email = curr.fetchone()[0]
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Retrieived user-credentials with USERKEY: {identifier} and EMAIL: {email}')
                return UserCredential(identifier, email)
            
            except (Exception, psycopg2.DatabaseError) as error:
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
                return None
        elif type == UserAuthStore.EMAIL:
            command = """SELECT user_key FROM user_creds
                         WHERE email = %s"""

            try:
                curr = self.conn.cursor()
                curr.execute(command, [identifier])
                user_key = curr.fetchone()[0]
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Retrieved user-credentials with USERKEY: {user_key} and EMAIL: {identifier}')
                return UserCredential(user_key, identifier)


            except (Exception, psycopg2.DatabaseError) as error:
                self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
                return None
        else:
            return None


    def insert_user(self, email, password):
        #insert user into movielens symlink
        FUNC_TAG = "insert_user"
        command = """INSERT INTO user_creds(email, password)
                     VALUES(%s, %s)
                     RETURNING user_key"""

        try:
            curr = self.conn.cursor()
            curr.execute(command, [email, password])
            user_key = curr.fetchone()[0]
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Inserted user-credentials with USERKEY: {user_key} and EMAIL: {email}')
            return user_key
        
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info(f'{TAG}::{FUNC_TAG}:: Error occurred: {error}')
            return None
    

