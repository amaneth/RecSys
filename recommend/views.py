from django.shortcuts import render

# Create your views here.
from recommend.models import Article
from recommend.models import Popularity
from recommend.models import Interaction
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from recommend.serializers import ArticleSerializer
from recommend.serializers import InteractionSerializer
from django.http import Http404
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from recommend.utils.methods.popularity import PopularityRecommender
from recommend.utils.methods.contentive import ContentBasedRecommender
from recommend.utils.extractor import Extractor
from recommend.utils.models import MlModels
from recommend.tasks import popularity_relearn
from recommend.tasks import content_based_relearn
from recommend.tasks import collaborative_relearn

import pandas as pd
import pickle
from django_pandas.io import read_frame

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


recommend_params = [openapi.Parameter( 'id', in_=openapi.IN_QUERY,
    description='The person id', type=openapi.TYPE_STRING, ),
    openapi.Parameter( 'community', in_=openapi.IN_QUERY,
    description='Recommend from', type=openapi.TYPE_STRING, ),
    openapi.Parameter( 'top', in_=openapi.IN_QUERY, 
    description='The top n recommendations to be returned', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'verbose', in_=openapi.IN_QUERY, 
    description='If true returns the deatil of the articles recommended(title, url, content...)',
    type=openapi.TYPE_BOOLEAN, ),
    openapi.Parameter( 'popularity', in_=openapi.IN_QUERY,
        description='Whether popularity recommendation will be used',
        type=openapi.TYPE_BOOLEAN, ),
    openapi.Parameter( 'content-based', in_=openapi.IN_QUERY,
        description='whether content based filtering will be used',
        type=openapi.TYPE_BOOLEAN, ),
    openapi.Parameter( 'collaborative', in_=openapi.IN_QUERY,
        description='whether collaborative filtering will be used',
        type=openapi.TYPE_BOOLEAN, ),
    
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
        ]
profile_param = [openapi.Parameter( 'id', in_=openapi.IN_QUERY,
    description='The person id', type=openapi.TYPE_INTEGER, ),
    openapi.Parameter( 'top', in_=openapi.IN_QUERY,
    description='top n profiles of the user to be returned', type=openapi.TYPE_INTEGER, ),
]



class RecommendArticles(APIView):

    @swagger_auto_schema(manual_parameters=recommend_params ,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request, format=None):
        '''
            retrieve personalized recommended articles
        '''
        person_id = request.GET['id']
        topn = int(request.GET['top'])
        recommend_from = request.GET['community']
        verbose= True if request.GET['verbose']=='true' else False

        popularity_recommendation = True if request.GET['popularity']=='true' else False
        content_based_recommendation = True if request.GET['content-based']=='true' else False
        collaborative_recommendation = True if request.GET['collaborative']=='true' else False
        enable_rec = [popularity_recommendation, content_based_recommendation,
                      collaborative_recommendation]
        if recommend_from=='mindplex':
            interactions_df = read_frame(Interaction.objects.filter(source=recommend_from))
            articles_df = read_frame(Article.objects.filter(source=recommend_from))
        else:
            interactions_df = read_frame(Interaction.objects.filter(~Q(source='mindplex')))
            articles_df = read_frame(Article.objects.filter(~Q(source='mindplex')))
        #interactions_df = pd.read_csv('recommend/files/interactions.csv')
        #articles_df = pd.read_csv('recommend/files/articles.csv')
        interactions_df.set_index('person_id', inplace=True)
        extractor = Extractor()
        if enable_rec.count(True)>1:
            pass # TODO create instance of hybrid recommender
        elif popularity_recommendation:
            if recommend_from =='mindplex':
                popularity_df = read_frame(Popularity.objects.filter(source='mindplex'))
            else:
                popularity_df = read_frame(Popularity.objects.filter(~Q(source='mindplex')))
            recommender = PopularityRecommender(popularity_df,articles_df)
        elif content_based_recommendation:
            recommender = ContentBasedRecommender(articles_df)
        elif collaborative_recommendation:
            pass #TODO create instance of collaborative recommender
        if recommend_from=='mindplex':
            recommendations_df = recommender.recommend_items(user_id=person_id,
                    recommend_from='mindplex',
                    items_to_ignore=extractor.get_items_interacted(person_id,
                                        interactions_df), topn=topn, verbose=verbose)
        else:
            recommendations_df = recommender.recommend_items(recommend_from='crawled',
                    user_id=person_id, items_to_ignore=extractor.get_items_interacted(person_id,
                                        interactions_df), topn=topn, verbose=verbose)
        return Response(recommendations_df)

    
class PostInteractions(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'person_id': openapi.Schema(type=openapi.TYPE_STRING, description='The person id'),
            'content_id': openapi.Schema(type=openapi.TYPE_STRING, description='The article id'),
            'event_type': openapi.Schema(type=openapi.TYPE_STRING,\
                    description='The interaction type'),
            'timestamp': openapi.Schema(type=openapi.TYPE_INTEGER,\
                    description='The timestamp the interaction has happened'),
            'source': openapi.Schema(type=openapi.TYPE_STRING,\
                    description='The source of the article the interaction has happened for'),


        }))
    def post(self, request, format=None):
        try:
            article_interacted= Article.objects.get(content_id=request.data['content_id'])
        except:
            return Response({"Error":"Article with this id doesn't exist"},
                                status=status.HTTP_400_BAD_REQUEST)
        request.data['article']=article_interacted.id
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
        properties={
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
        }))
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
            if relearn_popularity:
                popularity_relearn()
            if relearn_content_based:
                content_based_relearn()
            if relearn_collaborative:
                collaborative_relearn()
            return Response({'Relearn poularity':str(relearn_popularity),
                            'Relearn content based':str(relearn_content_based),
                            'Relearn collaborative':str(relearn_collaborative)})



class AutoRelearn(APIView):
    @swagger_auto_schema(manual_parameters=model_params,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request):
            start_popularity = True if request.GET['popularity']=='true' else False
            start_content_based = True if request.GET['content-based']=='true' else False
            start_collaborative = True if request.GET['collaborative']=='true' else False
            schedule_popularity = PeriodicTask.objects.get(name='relearn popularity')
            schedule_content_based = PeriodicTask.objects.get(name='relearn content based')
            schedule_collaborative = PeriodicTask.objects.get(name='relearn collaborative')
            schedule_popularity.enabled = start_popularity
            schedule_content_based.enabled = start_content_based
            schedule_collaborative.enabled = start_collaborative
            schedule_popularity.save()
            schedule_content_based.save()
            schedule_collaborative.save()
            return Response({'enable poularity':str(start_popularity),
                            'enable content based':str(start_content_based), 
                            'enable collaborative':str(start_collaborative)})

class ShowUserProfile(APIView):

    @swagger_auto_schema(manual_parameters=profile_param,security=[],
            responses={'400': 'Validation Error','200': ArticleSerializer})
    def get(self, request):
        person_id = request.GET['id']
        topn = int(request.GET['top'])
        with open('featurenames.pickle', 'rb') as handle:
            tfidf_feature_names = pickle.load(handle) 
        with open('userprofile.pickle', 'rb') as handle:
            user_profiles = pickle.load(handle)
        try:    
            user_profile = user_profiles[person_id]
        except KeyError:
            return Response({"The User's profile is empty "})
        user_profile_sorted =sorted(zip(tfidf_feature_names, 
            user_profiles[person_id].flatten().tolist()), key = lambda x: -x[1])[:topn]
        return Response({key:val for key, val in user_profile_sorted})






