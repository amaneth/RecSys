from django.db import models
from jsonfield import JSONField
#TODO content id as foreign key
# Create your models here.
class Interaction(models.Model):
    person_id = models.CharField(max_length=60, default='')
    content_id = models.CharField(max_length=60, default='')
    event_type = models.CharField(max_length=30, blank=True, default='')
    timestamp = models.IntegerField(default=0)
    source = models.CharField(max_length=40, default='')

    class Meta:
        unique_together= ('person_id','content_id','event_type',)

class Article(models.Model):
    timestamp = models.IntegerField()
    content_id = models.CharField(max_length=60, default='')
    author_person_id = models.CharField(max_length=60, default='')
    author_country = models.CharField(max_length=60, blank=True, default='')
    url = models.CharField(max_length =400, blank=True, default ='')
    title = models.CharField(max_length =400, blank=True, default='')
    content = models.TextField()
    source = models.CharField(max_length=40, default='mindplex')

class Popularity(models.Model):
    content_id = models.CharField(primary_key=True, max_length=60, default='')
    eventStrength = models.IntegerField()
