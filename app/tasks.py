# Flask App imports
from app import create_app, db
from rq import get_current_job
from app.models import User, Task, Result
from app.email import send_email
from flask import render_template
# General purpose libs
import os
import sys
import json
import time
import random
import datetime
import numpy as np
# Twython
from twython import Twython
from twython import TwythonError
# Text analysis libs
import nltk
from sklearn import svm
from sklearn.externals import joblib

# EmbSocketClient class
from app.EmbSocketClient import EmbSocketClient

# APP CONTEXT
app = create_app()
app.app_context().push()

# TWYTHON CREDENTIALS
APP_KEY = app.config['TWITTER_APP_KEY']
APP_SECRET = app.config['TWITTER_APP_SECRET']
OAUTH_TOKEN = app.config['TWITTER_OAUTH_TOKEN']
OAUTH_TOKEN_SECRET = app.config['TWITTER_OAUTH_TOKEN_SECRET']
MODELS_PATH = 'personality_models'
crawler = Twython(app_key=APP_KEY,
                app_secret=APP_SECRET,
                oauth_token=OAUTH_TOKEN,
                oauth_token_secret=OAUTH_TOKEN_SECRET)


# LOAD MODEL FILES
ext_model_file = os.path.join(MODELS_PATH, 'Word2Vec_Svm_EXT')
agr_model_file = os.path.join(MODELS_PATH, 'Word2Vec_Svm_AGR')
con_model_file = os.path.join(MODELS_PATH, 'Word2Vec_Svm_CON')
ope_model_file = os.path.join(MODELS_PATH, 'Word2Vec_Svm_OPE')
sta_model_file = os.path.join(MODELS_PATH, 'Word2Vec_Svm_STA')

ext_model = joblib.load(ext_model_file)
agr_model = joblib.load(agr_model_file)
con_model = joblib.load(con_model_file)
ope_model = joblib.load(ope_model_file)
sta_model = joblib.load(sta_model_file)

# EmbSocketClient CONFIG
EMBSC_ADDR = '127.0.0.1'
EMBSC_PORT = 9090


def dummyPersonality():
    v = []
    for i in range(5):
        v.append(random.randint(0,1))
    return v


def _set_task_progress(progress, status):
    print(progress, '% >>', status)
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.meta['status_description'] = status
        job.save_meta()
        task = Task.query.get(job.get_id())
        if progress >= 100:
            task.complete = True
            task.completed_with_status = progress
        db.session.commit()

## MANHATTAN DISTANCE
def manhattan_distance(x, y):
    return sum(abs(a - b) for a, b in zip(x, y))


def get_user(user_name=None, user_id=None):
    """Get user data in dictionary form"""
    user = dict()
    try:
        # CHECK IF USER EXISTS
        if user_id is None:
            response = crawler.lookup_user(screen_name=user_name)
        else:
            response = crawler.lookup_user(user_id=user_id)
        # GET USER DATA
        user_id = response[0]['id']
        user_name = response[0]['name']
        user_screen_name = response[0]['screen_name']
        user_tweets = response[0]['statuses_count']
        user_friends = response[0]['friends_count']
        user_avatar_small = response[0]['profile_image_url_https']
        user_avatar = user_avatar_small.replace('_normal', '')
        # print("found user {} with screen name {} with {} tweets".format(user_id, user_screen_name, user_tweets))
        user['user_id'] = user_id
        user['user_name'] = user_name
        user['screen_name'] = user_screen_name
        user['user_tweets'] = user_tweets
        user['user_friends'] = user_friends
        user['avatar'] = user_avatar
        return user
    except TwythonError as e:
        return e


def get_user_tweets(user_name=None, user_id=None):
    """Get user tweet list"""
    try:
        # GET USER TIMELINE
        # return "Hola"
        user_timeline = crawler.get_user_timeline(screen_name=user_name, user_id=user_id, tweet_mode='extended', count=100)
        user_tweets_list = list()
        for tweet in user_timeline:
            user_tweets_list.append(tweet['full_text'])
        return user_tweets_list
    except Exception as e:
        # return 'error al recibir {}\' timeline'.format(user_screen_name)
        return e


def get_user_friends(user_name=None, user_id=None):
    """Get user friends"""
    friends = crawler.get_friends_ids(screen_name=user_name, user_id=user_id)
    # FIRST 200 FRIENDS
    return friends['ids'][:200]


def get_user_personality(user_texts):
    """Get user personality given list of texts from user"""
    # return dummyPersonality()
    # EMB CLIENT INSTANCE
    emb_client = EmbSocketClient(EMBSC_ADDR, EMBSC_PORT)
    u_personality = list()
    # CORPUS AS WALL OF TEXT
    corpus = ''
    for text in user_texts:
        corpus += ''.join(text) + ' '
    corpus = corpus.strip()
    corpus = nltk.word_tokenize(corpus)
    # REPRESENTATION OF USER TEXTS AS W2V
    corpus_vec = None
    # QUERYING ALL WORDS IN USER TEXTS
    for word in corpus:
        try:
            if corpus_vec is None:
                corpus_vec = emb_client.query(word)
            else:
                corpus_vec = np.vstack((corpus_vec, emb_client.query(word)))
        # CURRENT WORD NOT REPRESENTED IN EMBEDDINGS
        except Exception as e:
            pass
    # AVG OF ALL WORD VECTORS
    corpus_vec_res = np.average(corpus_vec, axis=0)
    # PREDICTION OF EXT
    ext_pred = ext_model.predict([corpus_vec_res])
    ext_pred = ext_pred.tolist()
    u_personality.append(ext_pred[0])
    # PREDICTION OF AGR
    agr_pred = agr_model.predict([corpus_vec_res])
    agr_pred = agr_pred.tolist()
    u_personality.append(agr_pred[0])
    # PREDICTION OF CON
    con_pred = con_model.predict([corpus_vec_res])
    con_pred = con_pred.tolist()
    u_personality.append(con_pred[0])
    # PREDICTION OF OPE
    ope_pred = ope_model.predict([corpus_vec_res])
    ope_pred = ope_pred.tolist()
    u_personality.append(ope_pred[0])
    # PREDICTION OF STA
    sta_pred = sta_model.predict([corpus_vec_res])
    sta_pred = sta_pred.tolist()
    u_personality.append(sta_pred[0])
    return u_personality


def analyze_user(user_id=None, user_tag=None, max_friends=20):
    try:
        userm = User.query.get(user_id)
        steps = 5
        # GET MAIN USER
        current_step = 1
        _set_task_progress(current_step, 'Obteniendo informacion de {}'.format(user_tag))
        app.logger.info("Solicitando analisis de {}".format(user_tag))
        user = get_user(user_name=user_tag)

        # GET FRIENDS IDS
        _set_task_progress(int(current_step*100/steps), 'Obteniendo lista de amigos')
        friends_ids = get_user_friends(user_name=user['screen_name'])
        current_step += 1

        # pasos fijos + cantidad de amigos a recuperar + max_friends (si hay mas de 20) a analizar
        # por cada amigo hay que recuperar tweets, obtener personalidad y comparar con metrica con el usuario
        friends_n = len(friends_ids)
        if friends_n < 20:
            steps += friends_n + (friends_n*3)
        else:
            steps += friends_n + (max_friends*3)
        current_step += 1
        # GET USER TWEETS LIST
        _set_task_progress(int(current_step*100/steps), 'Obteniendo tweets de {}'.format(user['user_name']))
        user_tweets = get_user_tweets(user_name=user['screen_name'])
        current_step += 1
        # GET USER PERSONALITIES
        _set_task_progress(int(current_step*100/steps), 'Obteniendo perfil de personalidad de {}'.format(user['user_name']))
        user_personality = get_user_personality(user_tweets)
        current_step += 1

        friends_list = list()
        for friend in friends_ids:
            # GET SPECIFIC FRIEND
            f = get_user(user_id=friend)       # user dict
            _set_task_progress(int(current_step*100/steps), 'Obteniendo informacion de {}'.format(f['user_name']))
            friends_list.append(f)
            current_step += 1
        # SORT LIST OF FRIENDS BY POST COUNT
        friends_list = sorted(friends_list, key=lambda k: k['user_tweets'], reverse=True)
        # ONLY MOST RELEVANT MAX_FRIENDS
        friends_list = friends_list[:max_friends]

        # GET FRIENDS INFO
        friends_data = list()
        for friend in friends_list:
            # GET FRIEND TWEETS
            _set_task_progress(int(current_step*100/steps), 'Obteniendo tweets de {}'.format(friend['user_name']))
            friend_tweets = get_user_tweets(user_id=friend['user_id'])
            current_step += 1
            # GET FRIEND PERSONALITY
            _set_task_progress(int(current_step*100/steps), 'Obteniendo perfil de personalidad de {}'.format(friend['user_name']))
            friend_personality = get_user_personality(friend_tweets)
            friend_s = {'name': friend['screen_name'], 'personality': friend_personality, 'tweets_count': friend['user_tweets'], 'avatar': friend['avatar']}
            friends_data.append(friend_s)
            current_step += 1

        # OBTAIN DISTANCE METRICS
        for friend in friends_data:
            _set_task_progress(int(current_step*100/steps), 'Comparando {} con {}'.format(user['user_name'], friend['name']))
            distance = manhattan_distance(user_personality, friend['personality'])
            friend['distance'] = distance
            current_step += 1

        # SORT FRIENDS LIST ACCORDING TO DISTANCE
        friends_data = sorted(friends_data, key=lambda k: k['distance'])

        _set_task_progress(100, 'Analisis completo')
        user_analysis = {'user_name': user['user_name'], 'user_screen_name': user['screen_name'], 'user_personality': user_personality, 'user_tweets_count': user['user_tweets'], 'user_friends_count': user['user_friends'], 'user_avatar': user['avatar'], 'user': 1, 'friends': friends_data}
        job = get_current_job()
        result = Result(id=job.get_id(), result=json.dumps(user_analysis))
        db.session.add(result)
        db.session.commit()

        # SEND RESULTS EMAIL
        send_email('[ourPersonalities] Análisis completado',
                    sender=app.config['ADMINS'][0],
                    recipients=[userm.email],
                    text_body=render_template('email/task_completed.txt',
                                                user=userm, task=job.get_id()),
                    html_body=render_template('email/task_completed.html',
                                                user=userm, task=job.get_id()))
    except:
        _set_task_progress(500, 'Analisis fallido')
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
        print("error")
