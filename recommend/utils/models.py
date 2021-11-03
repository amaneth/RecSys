import pandas as pd
from django.conf import settings
from recommend.models import Popularity
from recommend.serializers import UserProfileSerializer
from sqlalchemy import create_engine
from celery.utils.log import get_task_logger
from django.core.cache import cache

import numpy as np
import scipy
import math
import random
import sklearn
from nltk.corpus import stopwords
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds
from sklearn.preprocessing import MinMaxScaler

import logging
import logging.handlers as loghandlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
loghandle = loghandlers.TimedRotatingFileHandler(
                filename="RecSys.log",
                when='D', interval=1, backupCount=7,
                encoding="utf-8")
loghandle.setFormatter(
    logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(loghandle)



class MlModels:
    def __init__(self):
        logger.info("Initializing building models...")
        #interaction_df = read_frame(Interaction.objects.all())
        self.interactions_df = pd.read_csv('recommend/files/interactions.csv')
        #articles_df = read_frame(Article.objects().all())
        self.articles_df = pd.read_csv('recommend/files/articles.csv')
        #articles_df = read_frame(Article.objects().all())
        articles_df = pd.read_csv('recommend/files/articles.csv')
        #interaction_train_df = train_test_split(self.interactions_df)                    
        self.interactions_train_df = pd.read_csv('recommend/files/interactions_train.csv')
        self.item_ids = articles_df['contentId'].tolist()
        

    def popularity(self):
        interactions_df.set_index('personId', inplace=True)
        popularity_df = self.interactions_df.groupby('contentId')['eventStrength'].sum(). \
                            sort_values(ascending= False).reset_index()

        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        database_name = settings.DATABASES['default']['NAME']
        database_url = 'postgresql://{user}:{password}@db:5432/{database_name}'.format(
        user=user,
        password=password,
        database_name=database_name,
        ) # setting the appropriate connection parameters
        engine = create_engine(database_url, echo=False)

        popularity_df.to_sql(Popularity._meta.db_table, con=engine, if_exists='replace') # saving to the database
        unlock = cache.delete("popularity")
        logger.debug("Release lock is  done is :"+ str(unlock))
    
    def tfidf(self):
        stopwords_list = stopwords.words('english') + stopwords.words('portuguese')
        vectorizer = TfidfVectorizer(analyzer='word',
                            min_df=0.003,
                            max_df=0.5,
                            max_features=5000,
                            stop_words=stopwords_list)
        tfidf_matrix = vectorizer.fit_transform(articles_df['title'] +""+ articles_df['text'])
        return tfidf_matrix
    def get_item_profile(self, item_id):
        idx = self.item_ids.index(item_id)
        item_profile = tfidf()[idx:idx+1]
        return item_profile
    def get_item_profiles(self, ids):
        item_profiles_list = [get_item_profile(x) for x in ids]
        item_profiles = scipy.sparse.vstack(item_profiles_list)
        return item_profiles
    def build_users_profile(self, person_id, interactions_indexed_df):
        interactions_person_df = interactions_indexed_df.loc[person_id]
        user_item_profiles = get_item_profiles(interactions_person_df['contentId'])
        user_item_strengths = np.array(interactions_person_df['eventStrength']).reshape(-1,1)
        #Weighted average of item profiles by interaction stength 
        user_item_strengths_weighted_avg = np.sum(user_item_profiles.multiply(user_item_strengths),
                                                  axis=0) / np.sum(user_item_strengths)
        user_profile_norm = sklearn.preprocessing.normalize(user_item_strengths_weighted_avg)
        return user_profile_norm
    def build_users_profiles(self):
        interactions_indexed_df = self.interactions_train_df[interactions_train_df['contentId']\
                                                       .isin(articles_df['contentId'])]\
                                                       .set_index('personId')
        user_profiles = {}
        for person_id in interactions_indexed_df.index.unique():
            user_profiles[person_id] = build_users_profile(person_id, interactions_indexed_df)
            user_model = UserProfileSerializer(user_profiles)
            user_model.save()
