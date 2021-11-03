from rest_framework import serializers
from recommend.models import Article, Interaction, UserProfile

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ['person_id', 'content_id', 'event_strength']
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['timestamp', 'content_id', 'author_person_id', 'author_country', 'url', 'title', 'content']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile'] 
