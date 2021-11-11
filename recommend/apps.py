from django.apps import AppConfig
from django.db.models.signals import post_migrate


def schedule_popularity(sender, **kwargs):
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    schedule, created = IntervalSchedule.objects.get_or_create(every=300,
                period=IntervalSchedule.SECONDS,
                )
    PeriodicTask.objects.update_or_create(
                name='relearn popularity',
                defaults={'task':'recommend.tasks.popularity_relearn', 'interval':schedule},
                )
def schedule_content_based(sender, **kwargs):
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    schedule, created = IntervalSchedule.objects.get_or_create(every=300,
                period=IntervalSchedule.SECONDS,
                )
    PeriodicTask.objects.update_or_create(
                name='relearn content based',
                defaults={'task':'recommend.tasks.content_based_relearn', 'interval':schedule},
                )
def schedule_collaborative(sender, **kwargs):
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    schedule, created = IntervalSchedule.objects.get_or_create(every=300,
                period=IntervalSchedule.SECONDS,
                )
    PeriodicTask.objects.update_or_create(
                name='relearn collaborative',
                defaults={'task':'recommend.tasks.collaborative_relearn', 'interval':schedule},
                )


class RecommendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommend'
    verbose_name = "recommender"
    def ready(self):
        post_migrate.connect(schedule_popularity, sender=self)
        post_migrate.connect(schedule_content_based, sender=self)
        post_migrate.connect(schedule_collaborative, sender=self)

