from recommend.utils.models import logger
from recommend.models import Reputation, Article, Popularity
from django_pandas.io import read_frame

import pickle
import pandas as pd
import math

class ReputationalRecommender:

    MODEL_NAME = 'High-Quality'
    def __init__(self, community):
        self.community = community
        #self.off_chain= Reputation.objects.get
        with open('highqualitymodel.pickle', 'rb') as handle:
            self.high_quality_model = pickle.load(handle)
        self.articles_df = read_frame(Article.objects.filter(community_id=self.community))
        self.popularity_df = read_frame(Popularity.objects.filter(community_id=self.community))
    def get_model_name(self):
        return self.MODEL_NAME
    def get_article_distribution(self, required, offchains, available_articles):
        distributed_amounts = {}
        total_offchains = sum(offchains.values())
        if sum(available_articles.values())<=required:
            for author,offchain in zip(available_articles.keys(), offchains.values()):
                distributed_amounts[author]= (available_articles[author], offchain)
            return distributed_amounts

        for indx, offchain in offchains.items():
            weight = offchain / total_offchains
            distributed_amount = round(weight * required)
            distributed_amount = min(distributed_amount, available_articles[indx])
            distributed_amounts[indx]=(distributed_amount, offchain)
            total_offchains -= offchain
            required -= distributed_amount
        return distributed_amounts

    def get_authors_articles(self, items_to_ignore):
        authors = self.articles_df.author_person_id.unique()
        author_articles={}
        for author in authors:
            author_article_ids=list(self.articles_df[self.articles_df['author_person_id']==author]['content_id'])
            #print("author article ids: {}". format(str(author_article_ids)))
            author_articles[author]= self.popularity_df[(self.popularity_df['content_id']\
                    .isin(author_article_ids)) & (~self.popularity_df['content_id']\
                    .isin(items_to_ignore))].sort_values('eventStrength', ascending=False)       
            #print("author recommended articles: {}".format(str(author_recommended_articles_df)))
        return author_articles    #return distribution

    def recommend_articles(self, user_id, items_to_ignore,page_size=10, topn=1000):
        reputations_df=self.high_quality_model[self.community]
        offchains=reputations_df.set_index('author_person_id')['offchain'].to_dict()
        #author with the number of articles he wrote
        available_articles = self.articles_df[~self.articles_df['content_id']\
                .isin(items_to_ignore)]['author_person_id'].value_counts().to_dict()
        logger.info("available articles: {}".format(available_articles))
        logger.info("offchains: {}".format(offchains))
        #remove authors with offchain value but has no articles written by them 
        for key in list(offchains):
            if not key in available_articles:
                offchains.pop(key)
        #remove availabe articles with no author with offchain value given
        for key in list(available_articles):
            if not key in offchains:
                available_articles.pop(key)
        logger.info("available articles: {}".format(available_articles))
        logger.info("offchains: {}".format(offchains))
        recommendations_df = pd.DataFrame()
        # author with the article's content_id he wrote
        author_articles= self.get_authors_articles(items_to_ignore)
        logger.info("author and the articles it wrote: {}".format(author_articles))
        number_of_recommended_articles = min(topn, sum(available_articles.values()))
        number_of_pages= math.ceil(number_of_recommended_articles/page_size)
        logger.info("high quality recommendation number of pages: {}".format(number_of_pages))
        logger.info("high quality recommendation available articles: {}".format(available_articles))
        for page in range(number_of_pages):
            distributed_amounts = self.get_article_distribution(page_size, offchains, available_articles)
            logger.info("Distributed amounts of article based on reputation weight: {}"\
                    .format(distributed_amounts))
            #sort them by their offchain value, sothat article by higher reputation  author will come to the front
            distributed_amounts_sorted = dict(sorted(distributed_amounts.items(),
                                                    key=lambda item : item[1][1], reverse=True))
            for author, (amount,offchain) in distributed_amounts_sorted.items():
                author_recommended_articles_df= author_articles[author].iloc[:amount]
                author_articles[author].drop(author_articles[author]\
                        .index[[x for x in range(amount)]], inplace=True)
                recommendations_df=recommendations_df.append(author_recommended_articles_df)
                available_articles[author]-=amount
        return recommendations_df
