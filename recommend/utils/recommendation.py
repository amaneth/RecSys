import pandas as pd
from recommend.models import Article, Interaction, Setting
from recommend.utils.methods.popularity import PopularityRecommender
from recommend.utils.methods.contentive import ContentBasedRecommender
from recommend.utils.methods.reputation import ReputationalRecommender
from django_pandas.io import read_frame
from recommend.utils.models import logger
from django.db.models import Q

class Recommendation:

    def __init__(self, recommender, recommend_from='mindplex'):
        
        self.recommender=recommender
        self.recommend_from=recommend_from
        self.popularity_weight = float(Setting.objects.get(section_name='weight', setting_name='popularity')\
                .setting_value)
        self.content_based_weight = float(Setting.objects.get(section_name='weight',
                                                    setting_name='content_based').setting_value)
        self.collaborative_weight = float(Setting.objects.get(section_name='weight',
                                                    setting_name='collaborative').setting_value)
        self.high_quality_weight = float(Setting.objects.get(section_name='weight',
                                                    setting_name='high_quality').setting_value)
        self.random_weight = float(Setting.objects.get(section_name='weight',
                                                    setting_name='random').setting_value)
        if recommend_from=='mindplex':
            self.articles_df = read_frame(Article.objects.filter(source='mindplex'))
            self.interactions_df = read_frame(Interaction.objects.filter(source='mindplex'))
        else:
            self.articles_df = read_frame(Article.objects.filter(~Q(source='mindplex')))
            self.interactions_df = read_frame(Interaction.objects.filter(~Q(source='mindplex')))
   
    def recommend(self, user_id,page_size, verbose=False):
        articles_to_ignore = self.get_items_interacted(user_id)
        if self.recommender=='default':
            recommenders_weight = [self.popularity_weight, self.content_based_weight,
                              self.collaborative_weight, self.high_quality_weight, self.random_weight]
            only_one= ([a==1.0 for a in recommenders_weight].count(True)==1) and \
                    ([a==0.0 for a in recommenders_weight].count(True)==4)
            #check the the weight given for the recommenders if the recommender chosen is only one of the
            #recommenders or the hybrid of them.
            if not only_one:
                return None
            # TODO a hybrid recommender
            elif recommenders_weight[0]==1.0:
                recommender = PopularityRecommender(recommend_from)
            elif recommenders_weight[1]==1.0:
                recommender = ContentBasedRecommender(recommend_from)
            elif recommenders_weight[2]==1.0:
                return None
                #TODO a collaborative recommender
            elif recommenders_weight[3]==1.0:
                return None #TODO
            elif recommenders_weight[4]==1.0:
                return None #TODO
            else:
                return None #TODO
        elif self.recommender=='popularity':
            recommender = PopularityRecommender(self.recommend_from)
            recommendations_df = recommender.recommend_articles(user_id, articles_to_ignore)
        elif self.recommender=='content-based':
            recommender = ContentBasedRecommender(self.recommend_from)
            recommendations_df = recommender.recommend_articles(user_id, articles_to_ignore)
        elif self.recommender == 'high-quality':
            recommender = ReputationalRecommender() 
            recommendations_df = recommender.recommend_articles(user_id, articles_to_ignore,page_size)
        else:
            return None

        if verbose:
            if self.articles_df.empty:
                raise Exception("articles is required in the verbose mode it doesn't exist")
            recommendations_df = recommendations_df.merge(self.articles_df[[ 'content_id',
                                                              'title',
                                                              'url',
                                                              'content',
                                                              'top_image']], how = 'left',
                                                          left_on = 'content_id',
                                                          right_on = 'content_id')
                                                          
            logger.info("the recommendation datafame:{}"\
                    .format(recommendations_df[recommendations_df['title'].isnull()]))
        return recommendations_df

    def get_items_interacted(self, person_id):
        try:
            interacted_articles = self.interactions_df.loc[person_id]['content_id']
            return set(interacted_articles if type(interacted_articles) \
                    is pd.Series else [interacted_items])
        except KeyError:
            return set()
        # retrun empty set if the user has no interaction so far
