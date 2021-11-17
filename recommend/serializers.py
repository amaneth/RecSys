from rest_framework import serializers
from recommend.models import Article, Interaction, UserProfile
from django.db.models import Q

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ['person_id', 'content_id', 'event_type']
    def create(self, validated_data):
        event = validated_data.get('event_type', None)
        if event=='unlike' or event == 'dislike':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='like'))
            q.delete()

        if event=='unpositive' or event == 'negative':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='positive'))
            q.delete()

        if event=='undislike':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='dislike'))
            q.delete()

        if event=='unnegative':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='negative'))
            q.delete()

        if event=='uncomment':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='comment'))
            q.delete()
        if event =='like':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                & Q(content_id=validated_data.get('content_id'))\
                & Q(event_type='dislike'))
            q.delete()
        
        if event =='positive':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                & Q(content_id=validated_data.get('content_id'))\
                & Q(event_type='negative'))
            q.delete()

        if event in ['like','positive','negative', 'dislike', 'comment']:
            
            return Interaction.objects.create(**validated_data)

        else:
            return Interaction(**validated_data)




    def get_unique_together_validators(self):
        return []


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['timestamp', 'content_id', 'author_person_id', 'author_country', 'url', 'title', 'content']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile'] 
