from django.apps import AppConfig
from django.db.models.signals import post_migrate

def schedule_relearn(sender, **kwargs):
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    schedule, created = IntervalSchedule.objects.get_or_create(every=10,
                period=IntervalSchedule.SECONDS,
                )
    PeriodicTask.objects.update_or_create(
                name='relearn content based',
                defaults={'task':'recommend.tasks.content_based_relearn', 'interval':schedule},
                )
    PeriodicTask.objects.update_or_create(
                name='relearn popularity',
                defaults={'task':'recommend.tasks.popularity_relearn', 'interval':schedule},
                )
    PeriodicTask.objects.update_or_create(
                name='relearn collaborative',
                defaults={'task':'recommend.tasks.collaborative_relearn', 'interval':schedule},
                )

    PeriodicTask.objects.update_or_create(
                name='relearn high quality',
                defaults={'task':'recommend.tasks.high_quality_relearn', 'interval':schedule},
                )
def recommendation_default_configuration(sender, **kwargs):
    from recommend.models import Setting
    Setting.objects.update_or_create(section_name='weight', setting_name='popularity',
            setting_type=3, defaults={'setting_value':'1.0'}
            )
    Setting.objects.update_or_create(section_name='weight', setting_name='content_based',
            setting_type=3, defaults={'setting_value':'0.0'})
    Setting.objects.update_or_create(section_name='weight', setting_name='collaborative',
            setting_type=3, defaults={'setting_value':'0.0'})
    Setting.objects.update_or_create(section_name='weight', setting_name='high_quality',
            setting_type=3, defaults={'setting_value':'0.0'})
    Setting.objects.update_or_create(section_name='weight', setting_name='random',
            setting_type=3, defaults={'setting_value':'0.0'})

class RecommendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommend'
    verbose_name = "recommender"
    def ready(self):
        post_migrate.connect(schedule_relearn, sender=self)
        post_migrate.connect(recommendation_default_configuration, sender=self)
