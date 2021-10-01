from django.db import models

# Create your models here.
class Interaction(models.Model):
    person_id = models.IntegerField()
    content_id = models.IntegerField()
    event_strength = models.FloatField()
class Article(models.Model):
    timestamp = models.IntegerField()
    content_id = models.IntegerField()
    autor_person_id = models.IntegerField()
    author_country = models.CharField(max_length=60, blank=True, default='')
    url = models.CharField(max_length =60, blank=True, default ='')
    title = models.CharField(max_length =60, blank=True, default='')
    content = models.TextField()

