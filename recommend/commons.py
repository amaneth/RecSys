import json
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from recommend.utils.models import logger

def autorelearn(community, start_popularity, start_content_based,
                start_collaborative, start_high_quality, start_random):

    logger.info("Enabling or disabling autorelearn of different models for the community -{}-\
            Popularity: {}, Content Based: {}, Collaborative: {}, High Quality: {}"\
            .format(community, start_popularity, start_content_based,
                start_collaborative, start_high_quality))

    schedule_popularity = PeriodicTask.objects.get(name='relearn popularity')
    schedule_content_based = PeriodicTask.objects.get(name='relearn content based')
    schedule_collaborative = PeriodicTask.objects.get(name='relearn collaborative')
    schedule_high_quality = PeriodicTask.objects.get(name='relearn high quality')

    popularity_orignal_args= json.loads(schedule_popularity.args)
    if start_popularity:
        popularity_orignal_args.append(community)
    else:
        if community in popularity_orignal_args:
            popularity_orignal_args.remove(community)
    schedule_popularity.args = list(set(popularity_orignal_args))
    logger.debug("popularity relearn community list:::{}".format(schedule_popularity.args))



    content_based_orignal_args= json.loads(schedule_content_based.args)
    if start_content_based:
        content_based_orignal_args.append(community)
    else:
        if community in content_based_orignal_args:
            content_based_orignal_args.remove(community)
    schedule_content_based.args = list(set(content_based_orignal_args))
    logger.debug("content based relearn community list:::{}".format(schedule_content_based.args))


    collaborative_orignal_args= json.loads(schedule_collaborative.args)
    if start_collaborative:
        collaborative_orignal_args.append(community)
    else:
        if community in collaborative_orignal_args:
            collaborative_orignal_args.remove(community)
    schedule_collaborative.args = list(set(collaborative_orignal_args))
    logger.debug("collaborative relearn community list:::{}".format(schedule_collaborative.args))


    high_quality_orignal_args= json.loads(schedule_high_quality.args)
    if start_high_quality:
        high_quality_orignal_args.append(community)
    else:
        if community in high_quality_orignal_args:
            high_quality_orignal_args.remove(community)
    schedule_high_quality.args = list(set(high_quality_orignal_args))
    logger.debug("high quality relearn community list:::{}".format(schedule_high_quality.args))

    try:
        schedule_popularity.save()
        schedule_content_based.save()
        schedule_collaborative.save()
        schedule_high_quality.save()
        response = {'enable poularity':start_popularity,
                    'enable content based':start_content_based, 
                    'enable collaborative':start_collaborative,
                    'enable high quality':start_high_quality,
                    'community': community}
        return response
    except Exception as e:
        return {'error':e}

def is_logical_weight(weights):
    #check if all values are between 1 ans o and the sume is 1.0, to be logical
    correct_setting= all(float(x)<=1.0 and float(x)>=0.0 for x in list(weights.values())) and \
            sum([float(y) for y in list(weights.values())])==1.0
    return correct_setting
