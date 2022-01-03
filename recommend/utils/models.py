import pandas as pd
from django.conf import settings
from recommend.models import Popularity, Interaction, Article, Reputation
from recommend.serializers import ReputationSerializer
from sqlalchemy import create_engine
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django_pandas.io import read_frame
from django.db.models import Q

import requests
import pickle
import numpy as np
import scipy
import math
import random
import sklearn
from nltk.corpus import stopwords
from scipy import sparse
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds
from sklearn.preprocessing import MinMaxScaler

import os
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

REPUTATION_API= 'http://api.reputation.icog-labs.com/core/communities/8/users/'

class MlModels:
    def __init__(self, model):
        logger.info("Initializing building models...")
        self.content_based_model_data={}
        self.interactions_df = read_frame(Interaction.objects.all())
        logger.debug("Shape of interactions df : -{0}- ".format(str(self.interactions_df.shape)))
        if model=='content-based':
            self.interactions_df = \
                    self.interactions_df[(self.interactions_df['event_type']!='dislike')\
                & (self.interactions_df['event_type']!='react-negative')]
        self.event_type_strength= {'view': 0.5,
                'like':1.0,
                'dislike':-1.0,
                'react-positive':1.5,
                'react-negative':-1.5,
                'comment-best':3.0,
                'comment-average':2.5, 
                'comment-good':2.0}
        self.interactions_df['eventStrength'] = self.interactions_df['event_type']\
                .apply(lambda x: self.event_type_strength[x])
        self.interactions_df = self.interactions_df.groupby(['content_id', 'person_id', 'source'])\
                            ['eventStrength'].sum().apply(lambda x : math.log(1+x, 2) if x>=0\
                            else -math.log(1+abs(x), 2) ).reset_index()
        logger.debug("Shape of interactions df after calculating event strenght: -{0}- "\
                .format(str(self.interactions_df.shape)))
        self.articles_df = read_frame(Article.objects.all())
        self.mindplex_articles_df= read_frame(Article.objects.filter(source='mindplex'))
        self.crawled_articles_df= read_frame(Article.objects.filter(~Q(source='mindplex')))
        #interaction_train_df = train_test_split(self.interactions_df)                    
        self.interactions_train_df = self.interactions_df
        self.item_ids= self.articles_df['content_id'].tolist()
        self.tfidf_matrix = None
        self.reputations_df = read_frame(Reputation.objects.all())
    def popularity(self):
        logger.info("building the popularity model has started")
        self.interactions_df.set_index('person_id', inplace=True)
        popularity_df = self.interactions_df.groupby(['content_id', 'source'])['eventStrength']\
                .sum().sort_values(ascending= False).reset_index()
        logger.debug("Shape of articles in the popularity: -{0}- ".format(str(popularity_df.shape)))
        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        database_name = settings.DATABASES['default']['NAME']
        database_url = 'postgresql://{user}:{password}@db:5432/{database_name}'.format(
        user=user,
        password=password,
        database_name=database_name,
        ) # setting the appropriate connection parameters
        engine = create_engine(database_url, echo=False)

        popularity_df.to_sql(Popularity._meta.db_table, con=engine, if_exists='replace', index=False) # saving to the database
        unlock = cache.delete("popularity")
        logger.info("Release lock is  done is :"+ str(unlock))
    
    def tfidf(self):
        logger.info("Building tfidf model..")
        stopwords_list = stopwords.words('english')
        vectorizer = TfidfVectorizer(analyzer='word',
                            min_df=0.003,
                            max_df=0.5,
                            max_features=5000,
                            stop_words=stopwords_list)
        self.tfidf_matrix = vectorizer.fit_transform(self.articles_df['title']\
                +" "+ self.articles_df['content'])
        tfidf_feature_names = vectorizer.get_feature_names()
        article_ids = {'mindplex':self.mindplex_articles_df['content_id'].tolist(),
                        'crawled':self.crawled_articles_df['content_id'].tolist()}
        mindplex_articles_df= self.articles_df[self.articles_df['source']=='mindplex']
        crawled_articles_df = self.articles_df[self.articles_df['source']!='mindplex']
        mindplex_tfidf_matrix= None
        crawled_tfidf_matrix= None
        if not mindplex_articles_df.empty:
            mindplex_tfidf_matrix= vectorizer.transform(mindplex_articles_df['content']+" "+\
                                        mindplex_articles_df['title'])
        if not crawled_articles_df.empty:
            crawled_tfidf_matrix= vectorizer.transform(crawled_articles_df['content']+" "+\
                                crawled_articles_df['title'])
        tfidf_by_source= {'mindplex': mindplex_tfidf_matrix,
                'crawled': crawled_tfidf_matrix}
        self.content_based_model_data= {'tfidf':tfidf_by_source,
                                    'ids': article_ids,
                                    'feature_names': tfidf_feature_names
                                 }
        #TODO incremental concept should be implemented here


    def get_item_profile(self, item_id):
        logger.info("building item's profile...")
        idx = self.item_ids.index(item_id)
        item_profile = self.tfidf_matrix[idx:idx+1]
        return item_profile
    def get_item_profiles(self, ids):
        logger.info("building items' profile")
        if isinstance(ids, str):
            ids = [ids]
        item_profiles_list = [self.get_item_profile(x) for x in ids]
        item_profiles = scipy.sparse.vstack(item_profiles_list)
        return item_profiles
    def build_users_profile(self, person_id, interactions_indexed_df):
        interactions_person_df = interactions_indexed_df.loc[person_id]
        user_item_profiles = self.get_item_profiles(interactions_person_df['content_id'])
        user_item_strengths = np.array(interactions_person_df['eventStrength']).reshape(-1,1)
        #Weighted average of item profiles by interaction stength 
        user_item_strengths_weighted_avg = np.sum(user_item_profiles.multiply(user_item_strengths),
                                                  axis=0) / np.sum(user_item_strengths)
        user_profile_norm = sklearn.preprocessing.normalize(user_item_strengths_weighted_avg)
        return user_profile_norm
    def build_users_profiles(self):
        logger.info("Building user profile")
        if self.articles_df.empty:
            raise Exception("There are no articles in the database. I can't build the users profile")
        self.tfidf()
        interactions_indexed_df = self.interactions_train_df[self.interactions_train_df['content_id']\
                                                       .isin(self.articles_df['content_id'])]\
                                                       .set_index('person_id')
        logger.info("Set index for interaction_ df is done...")
        user_profiles = {}
        for person_id in interactions_indexed_df.index.unique():
            user_profiles[person_id] = self.build_users_profile(person_id, interactions_indexed_df)
        self.content_based_model_data['user_profiles']= user_profiles

        with open('cbmodel.pickle', 'wb') as handle:
            pickle.dump(self.content_based_model_data, handle, protocol= pickle.HIGHEST_PROTOCOL)
            logger.info("Saving the users profile to the database profile is done"+\
                    str(os.getcwd()))
        unlock = cache.delete("content-based")
        logger.debug("Release lock for content-based is  done is :"+ str(unlock))

    def build_users_reputation(self):
        reputation_data = requests.get(REPUTATION_API).json()
        for data in reputation_data:
            data['community_id']=data.pop('community')
            data['author_person_id'] = data.pop('user')
        reputation_serialized = ReputationSerializer(data=reputation_data, many=True)
        if reputation_serialized.is_valid(raise_exception=True):
            reputation_serialized.save()
            logger.info("Reputation data has saved successfully")
        
        #refresh the reputation value and pickle it
        self.reputations_df = read_frame(Reputation.objects.all())
        communities= self.reputations_df.community_id.unique()
        reputation_model_data={}
        for community in communities:
            reputation_model_data[community]= self.reputations_df\
                    [self.reputations_df['community_id']==community]
        with open('highqualitymodel.pickle', 'wb') as handle:
            pickle.dump(reputation_model_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
