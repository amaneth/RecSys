from django.shortcuts import render

# Create your views here.
from recommend.models import Article
from recommend.models import Popularity
from recommend.models import Interaction
from recommend.models import Setting

from recommend.serializers import ArticleSerializer, InteractionSerializer, SettingSerializer
from django.http import Http404
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from recommend.utils.methods.popularity import PopularityRecommender
from recommend.utils.methods.contentive import ContentBasedRecommender
from recommend.utils.recommendation import Recommendation
from recommend.utils.models import MlModels, logger
from recommend.tasks import popularity_relearn, content_based_relearn, collaborative_relearn, high_quality_relearn
from recommend.commons import autorelearn
from recommend.commons import is_logical_weight

import json
import ast
import pandas as pd
import pickle
from django_pandas.io import read_frame

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# swagger param api definations
recommend_params = [openapi.Parameter( 'id', in_=openapi.IN_QUERY,
    description='The person id', type=openapi.TYPE_STRING, ),
    openapi.Parameter( 'from', in_=openapi.IN_QUERY,
    description='Recommend from(crawled/mindplex)', type=openapi.TYPE_STRING, ),
    openapi.Parameter( 'community', in_=openapi.IN_QUERY,
    description='community id of the media', type=openapi.TYPE_STRING, ),
    openapi.Parameter( 'page_size', in_=openapi.IN_QUERY, 
    description='Page size of the recommendations', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'page', in_=openapi.IN_QUERY, 
    description='Page number to be returned', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'verbose', in_=openapi.IN_QUERY, 
    description='If true returns the deatil of the articles recommended(title, url, content...)',
    type=openapi.TYPE_BOOLEAN, ),
    openapi.Parameter( 'recommender', in_=openapi.IN_QUERY,
        description='The recommender to be used',
        type=openapi.TYPE_STRING,
        enum=['default', 'popularity', 'content-based', 'collaborative', 'high-quality','random']
        ),
    
]

model_params = [openapi.Parameter( 'popularity', in_=openapi.IN_QUERY,
        description='if set true auto relearn for popularity model will be on',
        type=openapi.TYPE_BOOLEAN, ),
        openapi.Parameter( 'content-based', in_=openapi.IN_QUERY,
        description='if set true auto relearn for content based model will be on',
        type=openapi.TYPE_BOOLEAN, ),
        openapi.Parameter( 'collaborative', in_=openapi.IN_QUERY,
        description='if set true auto relearn for collaborative model will be on',
        type=openapi.TYPE_BOOLEAN, ),
        openapi.Parameter( 'high-quality', in_=openapi.IN_QUERY,
        description='if set true auto relearn for high quality model will be on',
        type=openapi.TYPE_BOOLEAN, ),
        openapi.Parameter( 'community', in_=openapi.IN_QUERY,
        description='The community which relearn is done for',
        type=openapi.TYPE_INTEGER, ),
        ]

model_param= {
            'popularity': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='The popularity model relearn'),
            'content_based': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='The content based relearn'),
            'collaborative': openapi.Schema(type=openapi.TYPE_BOOLEAN,\
                    description='The collaborative relearn'),
            'high_quality': openapi.Schema(type=openapi.TYPE_BOOLEAN,\
                    description='The high quality relearn'),
            'random': openapi.Schema(type=openapi.TYPE_BOOLEAN,\
                    description='The random relearn'),
            'community_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                description='The community id of the media')}


profile_param = [openapi.Parameter( 'id', in_=openapi.IN_QUERY,
    description='The person id', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'top', in_=openapi.IN_QUERY,
    description='top n profiles of the user to be returned', type=openapi.TYPE_INTEGER, ),
]

interaction_param= {
            'person_id': openapi.Schema(type=openapi.TYPE_STRING, description='The person id'),
            'content_id': openapi.Schema(type=openapi.TYPE_STRING, description='The article id'),
            'event_type': openapi.Schema(type=openapi.TYPE_STRING,\
                    description='The interaction type'),
            'timestamp': openapi.Schema(type=openapi.TYPE_INTEGER,\
                    description='The timestamp the interaction has happened'),
            'source': openapi.Schema(type=openapi.TYPE_STRING,\
                    description='The source of the article the interaction has happened for'),}

article_param = {
            'timestamp': openapi.Schema(type=openapi.TYPE_INTEGER,
                description='The time the article posted'),
            'content_id': openapi.Schema(type=openapi.TYPE_STRING, description='The article id'),
            'author_person_id': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s author id'),
            'author_country': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s author country'),
            'url': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s URL'),
            'title': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s title'),
            'content': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s content'),
            'source': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s content'),
            'top_image': openapi.Schema(type=openapi.TYPE_STRING,
                    description='The article\'s content'),
        }



class RecommendArticles(APIView, PageNumberPagination):

    @swagger_auto_schema(manual_parameters=recommend_params ,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request, format=None):
        '''
            retrieve personalized recommended articles
        '''
        person_id = request.GET['id']
        self.page_size = int(request.GET['page_size'])
        recommend_from = request.GET['from']
        verbose= True if request.GET['verbose']=='true' else False
        recommender = request.GET['recommender']
        community = request.GET['community']
        recommendation = Recommendation(recommender, recommend_from, community)
        recommendations_df = recommendation.recommend(person_id,self.page_size, verbose)
        recommendations = recommendations_df.to_dict('records')
        result_page = self.paginate_queryset(recommendations, request)
        return self.get_paginated_response(result_page)

    
class PostInteractions(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=interaction_param))
    def post(self, request, format=None):
        serializer = InteractionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostArticles(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=article_param))
    def post(self, request, format=None):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#TODO only relearn if there is a data change in the database
class Relearn(APIView):
    @swagger_auto_schema(manual_parameters=model_params,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request): 
            relearn_popularity = True if request.GET['popularity']=='true' else False
            relearn_content_based = True if request.GET['content-based']=='true' else False
            relearn_collaborative = True if request.GET['collaborative']=='true' else False
            relearn_high_quality = True if request.GET['high-quality']=='true' else False
            community = request.GET['community']
            if relearn_popularity:
                popularity_relearn(community)
            if relearn_content_based:
                content_based_relearn(community)
            if relearn_collaborative:
                collaborative_relearn(community)
            if relearn_high_quality:
                high_quality_relearn(community)
            return Response({'Relearn poularity':str(relearn_popularity),
                            'Relearn content based':str(relearn_content_based),
                            'Relearn collaborative':str(relearn_collaborative),
                            'Relearn High Quality': str(relearn_high_quality)})



class AutoRelearn(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=model_param))

    def post(self, request, format=None):
            start_popularity = request.data['popularity']
            start_content_based = request.data['content_based']
            start_collaborative = request.data['collaborative']
            start_high_quality =  request.data['high_quality']
            start_random = request.data['random']
            community = request.data['community_id']
            relearn = autorelearn(community, start_popularity, start_content_based,
                                start_collaborative, start_high_quality, start_random)
            return Response(relearn)

class ShowUserProfile(APIView):

    @swagger_auto_schema(manual_parameters=profile_param,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request):
        person_id = request.GET['id']
        topn = int(request.GET['top'])
        with open('cbmodel.pickle', 'rb') as handle:
            model=pickle.load(handle)
        try:    
            user_profile = model['user_profiles'][person_id]
        except KeyError:
            return Response({"The User's profile is empty "})
        user_profile_sorted =sorted(zip(model['feature_names'], 
            model['user_profiles'][person_id].flatten().tolist()), key = lambda x: -x[1])[:topn]
        return Response({key:val for key, val in user_profile_sorted})


class RecommendationSettings(APIView):
    def post(self, request, format=None):
        print("The request data is: {}". format(request.data))
        request= request.data.copy()
        section_name = request['section_name']
        if(section_name=='weight'):
            weights = {'popularity': request['popularity'], 'content_based':request['content_based'],
                    'collaborative':request['collaborative'], 'high_quality':request['high_quality'],
                    'random':request['random']}
            correct_setting = is_logical_weight(weights)
            if not correct_setting:
                return Response({"Error": "The setting data is not logical"}, status= status.HTTP_400_BAD_REQUEST)
            for key,value in weights.items():
                serializer = SettingSerializer(data={'section_name': 'weight', 'setting_name':key,
                                                'setting_value': value, 'setting_type':3})
                if serializer.is_valid():
                    serializer.save()
            return Response(request, status= status.HTTP_201_CREATED)
        else:
            serializer = SettingSerializer(request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
