# Generated by Django 3.2.7 on 2021-12-03 07:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recommend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='content_id',
            field=models.ForeignKey(db_column='content_id', on_delete=django.db.models.deletion.CASCADE, to='recommend.article'),
        ),
    ]
