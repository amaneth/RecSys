from django.db import models
from jsonfield import JSONField
#TODO content id as foreign key
# Create your models here.
class Interaction(models.Model):
    person_id = models.CharField(max_length=90,blank=True, default='')
    content_id = models.IntegerField()
    event_strength = models.FloatField()

class Article(models.Model):
    timestamp = models.IntegerField()
    content_id = models.IntegerField()
    author_person_id = models.IntegerField(default =0)
    author_country = models.CharField(max_length=60, blank=True, default='')
    url = models.CharField(max_length =400, blank=True, default ='')
    title = models.CharField(max_length =60, blank=True, default='')
    content = models.TextField()

class Popularity(models.Model):
    contentId = models.IntegerField(primary_key=True)
    eventStrength = models.IntegerField()

class UserProfile(models.Model):
    profile = JSONField()
