from django.db import models
from jsonfield import JSONField
#TODO content id as foreign key
# Create your models here.
class Article(models.Model):
    timestamp = models.IntegerField()
    content_id = models.CharField(max_length=60, default='')
    author_person_id = models.CharField(max_length=60, default='')
    author_country = models.CharField(max_length=60, blank=True, default='')
    url = models.CharField(max_length =400, blank=True, default ='')
    title = models.CharField(max_length =400, blank=True, default='')
    content = models.TextField()
    source = models.CharField(max_length=40, default='mindplex')
    top_image = models.CharField(max_length=400, blank='True',default='')
    #def __str__(self):
    #    return str(self.id)
class Interaction(models.Model):
    reactions= (('like', 'like'),
            ('react-positive','react-positive'),
            ('react-negative','react-negative'),
            ('dislike', 'dislike'),
            ('comment-best','comment-best'),
            ('comment-average','comment-average'),
            ('comment-good','comment-good'),
            ('view','view'),
            ('unlike', 'unlike'),
            ('unpositive', 'unpositive'),
            ('unnegative', 'unnegative'),
            ('undislike','undislike'),
            ('uncomment','uncomment'),
            ('follow', 'follow'),
            ('unfollow', 'unfollow')
        )
    person_id = models.CharField(max_length=60, default='')
    article = models.ForeignKey(Article,db_column='article_id',on_delete=models.CASCADE)
    content_id = models.CharField(max_length=60, default='')
    event_type = models.CharField(max_length=30, default='', choices=reactions)
    timestamp = models.IntegerField(default=0)
    source = models.CharField(max_length=40, default='')

    class Meta:
        unique_together= ('person_id','content_id','event_type',)


class Popularity(models.Model):
    content_id = models.CharField(primary_key=True, max_length=60, default='')
    source = models.CharField(max_length=40, default='')
    eventStrength = models.IntegerField()

class Setting(models.Model):
    section_name = models.CharField(max_length=60)
    setting_name = models.CharField(max_length=60)
    setting_value = models.CharField(max_length=200)
    setting_type = models.IntegerField()
