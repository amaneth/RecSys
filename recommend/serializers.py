from rest_framework import serializers
from recommend.models import Article, Interaction, Setting, Reputation, Popularity
from django.db.models import Q
class InteractionSerializer(serializers.ModelSerializer):
    article = serializers.ReadOnlyField(source='article.id', required=False)

    class Meta:
        model = Interaction
        fields = ['person_id','article', 'content_id', 'event_type', 'timestamp','source', 'community_id']

    def create(self, validated_data):
        event = validated_data.get('event_type', None)
        if event=='unlike' or event == 'dislike':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='like'))
            q.delete()

        if event=='unpositive':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='react-positive'))
            q.delete()

        if event=='undislike':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='dislike'))
            q.delete()

        if event=='unnegative':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & Q(event_type='react-negative'))
            q.delete()

        if event=='uncomment':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))\
                    & (Q(event_type='comment-best')|Q(event_type='comment-good')|\
                    Q(event_type='comment-average')))
            q.delete()
        if event =='like':
            try:
                q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                    & Q(content_id=validated_data.get('content_id'))& Q(event_type='dislike'))
                q.delete()
            except:
                pass

        if event =='unfollow':
            q = Interaction.objects.filter(Q(person_id=validated_data.get('person_id'))\
                & Q(content_id=validated_data.get('content_id'))\
                & Q(event_type='follow'))
            q.delete()

        if event in ['like','react-positive','react-negative', 'dislike', 'comment-best', 
                'comment-average', 'comment-good', 'view','follow']:
            article= validated_data.get('article',None)
            interaction, created = Interaction.objects\
                        .update_or_create(community_id = validated_data.get('community_id', None),
                                        article= validated_data.get('article', None),
                                        event_type=validated_data.get('event_type', None),
                                        person_id=validated_data.get('person_id', None),
                                        content_id=validated_data.get('content_id', None),
                            defaults={'timestamp': validated_data.get('timestamp', None),
                                        'source':  validated_data.get('source', None)})

            
            return interaction

        else:
            return Interaction(**validated_data)

    def validate(self, data):
        """
        Check the article being interacted is available
        """

        try:
            article_interacted= Article.objects.get(Q(content_id=data['content_id'])\
                    &(Q(community_id=data['community_id'])|Q(community_id=24)))
        except:
            raise serializers.ValidationError("This Article doesn't exist in this community")
        data['article']=article_interacted

        return data


    def get_unique_together_validators(self):
        return []


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['timestamp', 'content_id', 'author_person_id', 'author_country', 'url', 'title',
                'content','source', 'top_image', 'community_id']
    def create(self, validated_data):
        article, created = Article.objects.update_or_create(content_id= validated_data.get('content_id', None),
                                                    community_id= validated_data.get('community_id', None),
                            defaults={'timestamp': validated_data.get('timestamp', None),
                                    'author_person_id': validated_data.get('author_person_id', None),
                                    'author_country':validated_data.get('author_country', None),
                                    'url': validated_data.get('url', None),
                                    'title': validated_data.get('title', None),
                                    'content': validated_data.get('content', None),
                                    'source': validated_data.get('source', None),
                                    'top_image': validated_data.get('top_image', None)})
        return article

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['section_name', 'setting_name', 'setting_value', 'setting_type']
    def create(self, validated_data):
        setting, created = Setting.objects.update_or_create(section_name= validated_data.\
                                            get('section_name', None),
                                            setting_name= validated_data.get('setting_name', None),
                                            setting_type= validated_data.get('setting_type', None),
                                            defaults= {'setting_value': validated_data.get('setting_value',None)})
        return setting

class ReputationSerializer(serializers.ModelSerializer):
    categories = serializers.JSONField()
    class Meta:
        model = Reputation
        fields = '__all__'

    def create(self, validated_data):
        reputation, created = Reputation.objects.update_or_create(community_id= validated_data.\
                                            get('community_id', None), 
                                            author_person_id= validated_data.get('author_person_id', None),
                                            defaults={'offchain': validated_data.get('offchain', None),
                                                        'categories': validated_data.get('categories', None)})
class PopularitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Popularity
        fields = '__all__'
 
    def create(self, validated_data):
        popularity,created = Popularity.objects.update_or_create(community_id = validated_data.\
                                                    get('community_id', None),
                                                    content_id = validated_data.get('content_id', None),
                                                    defaults = {'source': validated_data.get('source', None),
                                                            'eventStrength': validated_data\
                                                                    .get('eventStrength', None)})
