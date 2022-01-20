from django_pandas.io import read_frame
import pickle
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
import logging
import logging.handlers as loghandlers
import numpy as np

from recommend.utils.models import logger


class ContentBasedRecommender:
    
    MODEL_NAME = 'Content-Based'
    
    def __init__(self, recommend_from, community):
        self.source= recommend_from
        self.community = community
        with open('cbmodel.pickle', 'rb') as handle:
            self.model=pickle.load(handle)
        
    def get_model_name(self):
        return self.MODEL_NAME
        
    def _get_similar_items_to_user_profile(self, person_id, topn=1000):
        #Computes the cosine similarity between the user profile and all item profiles
        try:
            cosine_similarities = cosine_similarity(self.model[self.community]['user_profiles'][person_id], 
                                    self.model[self.community]['tfidf'][self.source])
            logger.debug("The shape of the user pirofiles is: {}"\
                    .format(str(self.model[self.community]['user_profiles'][person_id].shape)))
        except KeyError:
            #length = len(list(self.model[self.community]['user_profiles']\
                    #.values())[0][0])
            number_of_features = self.model[self.community]['tfidf'][self.source].shape[1]
            dummy_profile = np.array([np.zeros(number_of_features)])
            cosine_similarities = cosine_similarity(dummy_profile, self.model[self.community]['tfidf'][self.source])
            logger.info("User is getting some random content-based recommendation\
                    because it has no previous history")
        #Gets the top similar items
        similar_indices = cosine_similarities.argsort().flatten()[-topn:]
        #Sort the similar items by similarity
        similar_items = sorted([(self.model[self.community]['ids'][self.source][i], cosine_similarities[0,i])\
                                for i in similar_indices],
                key=lambda x: -x[1])
        return similar_items
        
    def recommend_articles(self,user_id, articles_to_ignore):
        if self.model[self.community]['tfidf'][self.source] is None:
            return pd.DataFrame()
        similar_items = self._get_similar_items_to_user_profile(user_id)
        logger.info("{0} similar articles has been found:".format(str(similar_items)))
        #Ignores items the user has already interacted
        similar_items_filtered = list(filter(lambda x: x[0] not in articles_to_ignore, similar_items))
        
        recommendations_df = pd.DataFrame(similar_items_filtered,
                columns=['content_id', 'recStrength'])



        return recommendations_df
