from django_pandas.io import read_frame
import pickle
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
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



class ContentBasedRecommender:
    
    MODEL_NAME = 'Content-Based'
    
    def __init__(self, items_df=None):
        self.items_df = items_df
        with open('cbmodel.pickle', 'rb') as handle:
            self.model=pickle.load(handle)
        '''with open('userprofile.pickle', 'rb') as handle:
            self.user_profiles = pickle.load(handle)
        self.tfidf_matrix = sparse.load_npz("tfidf.npz")'''
        
    def get_model_name(self):
        return self.MODEL_NAME
        
    def _get_similar_items_to_user_profile(self, person_id,source='mindplex',topn=1000):
        #Computes the cosine similarity between the user profile and all item profiles
        cosine_similarities = cosine_similarity(self.model['user_profiles'][person_id], 
                                    self.model['tfidf'][source])
        #Gets the top similar items
        similar_indices = cosine_similarities.argsort().flatten()[-topn:]
        #Sort the similar items by similarity
        similar_items = sorted([(self.model['ids'][source][i], cosine_similarities[0,i])\
                                for i in similar_indices],
                key=lambda x: -x[1])
        return similar_items
        
    def recommend_items(self,user_id, recommend_from='mindplex', items_to_ignore=[], topn=10, verbose=False):
        similar_items = self._get_similar_items_to_user_profile(user_id, source=recommend_from)
        logger.info("{0} similar articles has been found:".format(str(similar_items)))
        #Ignores items the user has already interacted
        similar_items_filtered = list(filter(lambda x: x[0] not in items_to_ignore, similar_items))
        
        recommendations_df = pd.DataFrame(similar_items_filtered,
                columns=['content_id', 'recStrength']).head(topn)
        #recommendations_similar_filtered_df =pd.DataFrame(similar_items_filtered)
        #if source =='mindplex':
        #    recommendations_source_filtered_df = recommendations_similar_filtered_df.\
        #            loc[recommendations_similar_df['source']==source]
        #else:
        #    recommendations_source_filtered_df = recommendations_similar_filtered_df.\
        #            loc[recommendations_similar_df['source']!='mindplex']
        #recommendations_df= recommendations_source_filtered_df[['content_id','recStrength']]\
        #        .head(topn)


        if verbose:
            if self.items_df is None:
                raise Exception('"items_df" is required in verbose mode')

            recommendations_df = recommendations_df.merge(self.items_df, how = 'left', 
                                                          left_on = 'content_id', 
                                                          right_on = 'content_id')\
                                                          [['recStrength',
                                                              'content_id',
                                                              'title',
                                                              'url']]


        return recommendations_df
