from django_pandas.io import read_frame
from recommend.models import Popularity
from django.db.models import Q

class PopularityRecommender:
    MODEL_NAME = 'Popularity'
    
    def __init__(self, recommend_from, community):
        if recommend_from=='mindplex':
            self.popularity_df = read_frame(Popularity.objects.filter(source='mindplex', community_id=community))
        else:
            self.popularity_df = read_frame(Popularity.objects.filter(~Q(source='mindplex')))
        
    def get_model_name(self):
        return self.MODEL_NAME
    def recommend_articles(self, user_id, articles_to_ignore):
        # Recommend the more popular itmes that the user hasn't seen yet.
        recommendations_df = self.popularity_df[~self.popularity_df['content_id']\
                                .isin(articles_to_ignore)] \
                                .sort_values('eventStrength', ascending=False) 
        
        return recommendations_df
