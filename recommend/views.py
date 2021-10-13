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

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


recommend_params = [openapi.Parameter( 'id', in_=openapi.IN_QUERY,
    description='The person id', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'top', in_=openapi.IN_QUERY, 
    description='The top n recommendations to be returned', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'verbose', in_=openapi.IN_QUERY, 
    description='If true returns the deatil of the article recommended(title, url, content...)',
    type=openapi.TYPE_INTEGER, )]


class RecommendArticles(APIView):

    @swagger_auto_schema(manual_parameters=[id_param],security=[], responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request, format=None):
        '''
            retrieve personalized recommended articles
        '''
        #interaction_df = read_frame(Interaction.objects.all())
        #articles_df = read_frame(Article.objects().all())
        person_id = int(request.GET['id'])
        topn = int(request.GET['top'])
        verbose= True if request.GET['verbose'] else False
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
                                        topn=topn, verbose=verbose)
        return Response(recommendations_df)

    def post(self, request, format=None):
        serializer = InteractionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostArticles(APIView):

    def post(self, request, format=None):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






