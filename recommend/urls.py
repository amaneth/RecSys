from django.urls import path
from recommend import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('recommend/<str:person_id>', views.RecommendArticles.as_view()),
    #path('recommend/interactions', views.RecommendArticles.as_view({'post':'post_interactions')),
    #path('recommend/articles', views.RecommendArticles.as_view({'post':'post_articles'})),
]
