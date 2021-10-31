import pandas as pd
from django.conf import settings
from recommend.models import Popularity
from sqlalchemy import create_engine
from celery.utils.log import get_task_logger
from django.core.cache import cache

logger = get_task_logger(__name__)

class MlModels:
    def popularity(self):
        #interaction_df = read_frame(Interaction.objects.all())
        interactions_df = pd.read_csv('recommend/files/interactions.csv')
        interactions_df.set_index('personId', inplace=True)
        popularity_df = interactions_df.groupby('contentId')['eventStrength'].sum(). \
                            sort_values(ascending= False).reset_index()

        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        database_name = settings.DATABASES['default']['NAME']
        database_url = 'postgresql://{user}:{password}@db:5432/{database_name}'.format(
        user=user,
        password=password,
        database_name=database_name,
        ) # setting the appropriate connection parameters
        engine = create_engine(database_url, echo=False)

        popularity_df.to_sql(Popularity._meta.db_table, con=engine, if_exists='replace') # saving to the database
        unlock = cache.delete("popularity")
        logger.debug("Release lock is  done is :"+ str(unlock))

