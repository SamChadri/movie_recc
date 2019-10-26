import pytest
from flask import g, session
from flaskr.ml_backend import recc
from time import sleep

def test_home(client):
    assert client.get('/').status_code == 200

def test_create_user(client):
    with client:
        ob = None
        assert client.get('/recc/movies').status_code == 200
        assert session['user_id'] == 611
        assert recc.check_user(611, ob) == True 

def test_submit_rating(client):
    with client:
        request  =  client.post('/recc/movies', data={'rating': '5' , 'itemId': '122926' })

        assert session['122926'] ==  '5'

def test_load(client):
    with client:
        assert client.get('/recc/load').status_code == 200
        assert session['task'] != ''

    sleep(30)
    with client:
        assert client.get('/recc/recc_list').status_code == 200
        assert session["len_movies"] != 0
