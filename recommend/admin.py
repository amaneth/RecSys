from django.contrib import admin
from recommend.models import *
# Register your models here.
myModels = [Reputation, Article, Interaction, Popularity]
admin.site.register(myModels)
