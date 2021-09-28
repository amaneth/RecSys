class PopularityRecommender:
    MODEL_NAME = 'Popularity'
    '''
    item_popularity_df = interactions_full_df.groupby('contentId')['eventType'].sum().\
                        sort_values(ascending = False).reset_index()
    '''
    def __init__(self, popularity_df, items_df=None):
        self.popularity_df = popularity_df
        self.items_df = items_df
        
    def get_model_name(self):
        return self.MODEL_NAME
    def recommend_items(self, user_id, items_to_ignore=[], topn=10, verbose=False):
        # Recommend the more popular itmes that the user hasn't seen yet.
        recommendations_df = self.popularity_df[~self.popularity_df['contentId'].isin(items_to_ignore)] \
                                .sort_values('eventType', ascending=False) \
                                .head(topn)
        if verbose:
            if self.items_df is None:
                raise Exception('"items_df" is required in verbose mode')
            recommendations_df = recommendations_df.merge(self.items_df, how = 'left', 
                                                          left_on = 'contentId', 
                                                          right_on = 'contentId')[['eventType', 'contentId', 'title', 'url', 'lang']]
        return recommendations_df
