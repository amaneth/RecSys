import pandas as pd
from django.conf import settings
from recommend.models import Popularity, Interaction, Article, Reputation
from recommend.serializers import ReputationSerializer, PopularitySerializer
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

REPUTATION_API= 'http://api.reputation.icog-labs.com/core/communities/'

class MlModels:
    def __init__(self, model, community):
        logger.info("Initializing building models...")
        try:
            with open('cbmodel.pickle', 'rb') as handle:
                self.content_based_model_data = pickle.load(handle)
        except FileNotFoundError:
            self.content_based_model_data = {}
        # note that self.community is string, you should change it to int in data frame extraction as
        #it int in the database model, maybe some work to do changing both to int or string 
        self.community = community
        self.articles_df = read_frame(Article.objects.filter(Q(community_id=self.community)|Q(community_id=24)))
        #get interactions in the community, this includes interactions of the crawled articles in the community
        interactions_df = read_frame(Interaction.objects.filter(community_id=self.community))
        community_articles_df = self.articles_df[self.articles_df['community_id']==int(self.community)]
        community_articles_df.rename(columns={'author_person_id':'person_id'}, inplace=True)
        self.interactions_df = pd.concat([community_articles_df, interactions_df], ignore_index=True)\
                                    [['person_id','content_id', 'event_type', 'source', 'community_id']]\
                                    .fillna('post')
        logger.debug("Shape of interactions df : -{0}- ".format(self.interactions_df.shape))
        #ignore react-negative and dislike interactions for content_based as user dislikes an article doesn't 
        # say about user don't want to be recommended that article
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
                'comment-good':2.0,
                'post':0.0}
        self.interactions_df['eventStrength'] = self.interactions_df['event_type']\
                .apply(lambda x: self.event_type_strength[x])
        self.interactions_df = self.interactions_df.groupby(['content_id', 'person_id', 'source',\
                'community_id'])['eventStrength'].sum().apply(lambda x : math.log(1+x, 2) if x>=0\
                            else -math.log(1+abs(x), 2) ).reset_index()
        logger.debug("Shape of interactions df after calculating event strenght: -{0}- "\
                .format(str(self.interactions_df.shape)))
        #get articles from its community and the crawled articles(community_id=24), this helps the user profile 
        # to be prepared from interactions of the user to the crawled articles in its community.
        self.mindplex_articles_df= read_frame(Article.objects.filter(source='mindplex',
                                                community_id=self.community))
        self.crawled_articles_df= read_frame(Article.objects.filter(~Q(source='mindplex')))
        #interaction_train_df = train_test_split(self.interactions_df)                    
        self.interactions_train_df = self.interactions_df
        self.item_ids= self.articles_df['content_id'].tolist()
        self.tfidf_matrix = None
        self.reputations_df = read_frame(Reputation.objects.all())

    def popularity(self):
        logger.info("building the popularity model has started")
        self.interactions_df.set_index('person_id', inplace=True)
        popularity_df = self.interactions_df.groupby(['content_id', 'source', 'community_id'])['eventStrength']\
                .sum().sort_values(ascending= False).reset_index()
        logger.debug("Shape of articles in the popularity: -{0}- ".format(str(popularity_df.columns)))
        
        popularity_dict = popularity_df.to_dict(orient='records')
        popularity_serialized= PopularitySerializer(data=popularity_dict, many=True)
        if popularity_serialized.is_valid(raise_exception=True):
            popularity_serialized.save()
    
        unlock = cache.delete("popularity"+str(self.community))
        logger.info("Release lock "+("is not ", "is ")[unlock]+"done for :{}"\
                .format("popularity"+str(self.community)))

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
        self.content_based_model_data[self.community]= {'tfidf':tfidf_by_source,
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
        self.content_based_model_data[self.community]['user_profiles']= user_profiles

        with open('cbmodel.pickle', 'wb') as handle:
            pickle.dump(self.content_based_model_data, handle, protocol= pickle.HIGHEST_PROTOCOL)
            logger.info("Saving the users profile to the database profile is done"+\
                    str(os.getcwd()))
        unlock = cache.delete("content-based"+self.community)
        logger.debug("Release lock for content-based is  done is :"+ str(unlock))

    def build_users_reputation(self):
        reputation_data = requests.get(REPUTATION_API+str(self.community)+'/users/').json()
        for data in reputation_data:
            data['community_id']=data.pop('community')
            data['author_person_id'] = data.pop('user')
        reputation_serialized = ReputationSerializer(data=reputation_data, many=True)
        if reputation_serialized.is_valid(raise_exception=True):
            reputation_serialized.save()
            logger.info("Reputation data has saved successfully")
        
        #refresh the reputation value and pickle it for different communities separately
        #self.reputations_df = read_frame(Reputation.objects.all())
        self.reputations_df.sort_values(by=['offchain'], ascending=False, inplace=True)
        #update for the communiity requested
        reputation_model_data={}
        reputation_model_data[self.community]= self.reputations_df[self.reputations_df['community_id']==int(self.community)]
        logger.info("Reputation model :{}".format(reputation_model_data[self.community].to_dict('records')))
        with open('highqualitymodel.pickle', 'wb') as handle:
            pickle.dump(reputation_model_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        unlock = cache.delete("high-quality"+self.community)
        logger.debug("Release lock for content-based is  done is :"+ str(unlock))
