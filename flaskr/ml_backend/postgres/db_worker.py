import json
from concurrent.futures import *
from multiprocessing import Pool
#from psycopg2.errors import SyntaxError
import multiprocessing as mp
from ..movielens import User,ModernUser,Rating,Item,ModernItem,Link, Dataset
import psycopg2
import logging
import itertools
import math
from tqdm import tqdm
TAG = 'DBWorker'

class DBWorker():
    def __init__(self,key_file, postgres_ip, postgres_port, user_list, progress=None):
        with open(key_file) as f:
            data = json.load(f)
            self.__database = data['database']
            self.__user = data['user']
            self.__password = data['password']
        
        self.postgres_ip = postgres_ip
        self.postgres_port = postgres_port
        self.user_list = user_list
        self.records_affected = 0


    def update_pcs(self, curr_user):
        FUNC_TAG = 'update_pcs'
        update_command = """UPDATE users
                            SET pcs = %s
                            WHERE user_id = %s"""

        self.conn = psycopg2.connect(
            host=self.postgres_ip,
            port=self.postgres_port,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )
        
        g_logger = logging.getLogger('gunicorn.error')
        g_logger.info(f'{TAG}::{FUNC_TAG}:: Calculating pcs data for user = {curr_user}...')
        records_affected = 0

        pcs_data = {}
        for user in self.user_list:
            if curr_user != user:
                pcs_data[user] = self.db_pcs(curr_user, user, False)

        try:
            curr = self.conn.cursor()
            curr.execute(update_command, (json.dumps(pcs_data), curr_user))
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.conn.close()
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Finished processing and entering pcs data for modern user = {curr_user}')
        
        except (Exception, psycopg2.DatabaseError) as error:
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()
            self.conn.close()
            return 0

        return curr_user


    def update_modern_pcs(self, curr_user):
        FUNC_TAG = 'update_modern_pcs'
        update_command = """UPDATE modern_users
                            SET pcs = %s
                            WHERE user_id = %s"""

        self.conn = psycopg2.connect(
            host=self.postgres_ip,
            port=self.postgres_port,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )
        records_affected = 0
        g_logger = logging.getLogger('gunicorn.error')
        g_logger.info(f'{TAG}::{FUNC_TAG}:: Calculating modern pcs data for user = {curr_user}...')

        pcs_data = {}
        for user in self.user_list:
            if curr_user != user:
                pcs_data[user] = self.db_pcs(curr_user, user, True)
            
        try:
            curr = self.conn.cursor()
            curr.execute(update_command, (json.dumps(pcs_data), curr_user))
            records_affected = curr.rowcount
            curr.close()
            self.conn.commit()
            self.conn.close()
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Finished processing and entering modern pcs data for modern user = {curr_user}')
        
        except (Exception, psycopg2.DatabaseError) as error:
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()
            self.conn.close()
            return 0

        return curr_user

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

    
    def get_rating(self, user_id=None, rating_id=None, movie_id=None):
        user_query = """SELECT * FROM ratings
                        WHERE user_id = %s"""
        rating_query = """SELECT * FROM ratings
                        WHERE rating_id = %s"""
        movie_query = """SELECT * FROM ratings
                         WHERE item_id = %s"""
        
        FUNC_TAG = 'get_rating'
        g_logger = logging.getLogger('gunicorn.error')
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
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()

    def get_modern_rating(self, user_id=None, rating_id=None, movie_id=None):

        FUNC_TAG = 'get_modern_rating'
        user_query = """SELECT * FROM modern_ratings
                        WHERE user_id = %s"""
        rating_query = """SELECT * FROM modern_ratings
                        WHERE rating_id = %s"""
        movie_query = """SELECT * FROM modern_ratings
                         WHERE item_id = %s"""
        g_logger = logging.getLogger('gunicorn.error')

        try:
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
        except (Exception, psycopg2.DatabaseError) as error:
            g_logger.info(f'{TAG}::{FUNC_TAG}:: Error occured {error}')
            self.conn.cursor().close()