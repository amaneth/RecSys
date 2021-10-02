from django.shortcuts import render

# Create your views here.
from recommend.models import Article
from recommend.models import Interaction
from recommend.serializers import ArticleSerializer
from recommend.serializers import InteractionSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from recommend.utils.popularity import PopularityRecommender
from recommend.utils.extractor import Extractor
import pandas as pd
from django_pandas.io import read_frame


class RecommendArticles(APIView):
    """
    retrieve personalized recommended articles
    """
    def get(self, request, person_id, format=None):
        '''
        interaction_df = read_frame(Interaction.objects.all())
        articles_df = read_frame(Article.objects().all())
        '''
        person_id = int(person_id)
        interactions_df = pd.read_csv('recommend/files/interactions.csv')
        articles_df = pd.read_csv('recommend/files/articles.csv')
        interactions_df.set_index('personId', inplace=True)
        popularity_df = interactions_df.groupby('contentId')['eventStrength'].sum(). \
                                sort_values(ascending= False).reset_index()
        popularity_model = PopularityRecommender(popularity_df,articles_df)
        extractor = Extractor()
        recommendations_df = popularity_model.recommend_items(user_id=person_id,
                                items_to_ignore= \
                                        extractor.get_items_interacted(person_id, interactions_df),\
                                        topn=10, verbose=False)
        return Response(recommendations_df)
    '''
    def post_interactions(self, request, format=None):
        serializer = InteractionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post_articles(self, request, format=None):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    '''





