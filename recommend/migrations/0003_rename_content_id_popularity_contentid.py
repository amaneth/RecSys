# Generated by Django 3.2.7 on 2021-10-29 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recommend', '0002_popularity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='popularity',
            old_name='content_id',
            new_name='contentId',
        ),
    ]