import time
from recommender.celery import app
from recommend.utils.models import MlModels
from celery.utils.log import get_task_logger
from celery import shared_task
from django.core.cache import cache

from recommend.utils.models import logger

LOCK_EXPIRE = 60 



@shared_task
def popularity_relearn(*args):
    for community in args:
        logger.debug("arguments value: {}".format(community))
        #lock relearn popularity for the specific community
        acquired = cache.add("popularity"+str(community),"popularity",LOCK_EXPIRE)
        logger.debug("Popularity C----A---C---H--ED is : %s", acquired)
        if acquired:
            logger.info('Popularity model is relearning...')
            model=MlModels('popularity', str(community))
            model.popularity()
        else:
            logger.debug('Relearning the popularity model is already started by another worker')

@shared_task
def content_based_relearn(*args):
    for community in args:
        acquired = cache.add("content-based"+str(community),"content-based",LOCK_EXPIRE)
        logger.debug("Content based C----A---C---H--ED is : %s", acquired)
        if acquired:
            logger.info('Content based model is relearning...')
            model=MlModels('content-based', str(community))
            model.build_users_profiles()
        else:
            logger.debug('Relearning the content based model is already started by another worker')

@shared_task
def collaborative_relearn(*args):
    for community in args:
        acquired = cache.add("collaborative"+str(community),"collaborative",LOCK_EXPIRE)
        logger.debug("Collaborative C----A---C---H--ED is : %s", acquired)
        if acquired:
            logger.info('Collaborative model is relearning...')
            #TODO call the collaborative model
        else:
            logger.debug('Relearning the collaborative model is already started by another worker')



@shared_task
def high_quality_relearn(*args):
    for community in args:
        acquired = cache.add("high-quality"+str(community),"high-quality",LOCK_EXPIRE)
        logger.debug("High quality model relearn started cached is : %s", acquired)
        if acquired:
            logger.info('High Quality model is relearning...')
            model=MlModels('high-quality', str(community))
            model.build_users_reputation()
        else:
            logger.debug('Relearning the high quality model is already started by another worker')
        


