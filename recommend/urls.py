from django.urls import path
from recommend import views
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

...

schema_view = get_schema_view(
   openapi.Info(
      title="The recommender system",
      default_version='v1',
      description="Recommender system",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('recommendations', views.RecommendArticles.as_view()),
    path('articles', views.PostArticles.as_view()),
    path('interactions', views.PostInteractions.as_view()),
    path('auto-relearn', views.AutoRelearn.as_view()),
    path('relearn', views.Relearn.as_view()),
    path('profile', views.ShowUserProfile.as_view()),
    path('config', views.RecommendationSettings.as_view()),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


]
