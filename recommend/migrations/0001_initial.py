# Generated by Django 3.2.7 on 2021-12-02 15:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('timestamp', models.IntegerField()),
                ('content_id', models.CharField(default='', max_length=60, primary_key=True, serialize=False, unique=True)),
                ('author_person_id', models.CharField(default='', max_length=60)),
                ('author_country', models.CharField(blank=True, default='', max_length=60)),
                ('url', models.CharField(blank=True, default='', max_length=400)),
                ('title', models.CharField(blank=True, default='', max_length=400)),
                ('content', models.TextField()),
                ('source', models.CharField(default='mindplex', max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Popularity',
            fields=[
                ('content_id', models.CharField(default='', max_length=60, primary_key=True, serialize=False)),
                ('eventStrength', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_id', models.CharField(default='', max_length=60)),
                ('event_type', models.CharField(choices=[('like', 'like'), ('react-positive', 'react-positive'), ('react-negative', 'react-negative'), ('dislike', 'dislike'), ('comment-best', 'comment-best'), ('comment-average', 'comment-average'), ('comment-good', 'comment-good'), ('view', 'view'), ('unlike', 'unlike'), ('unpositive', 'unpositive'), ('unnegative', 'unnegative'), ('undislike', 'undislike'), ('uncomment', 'uncomment')], default='', max_length=30)),
                ('timestamp', models.IntegerField(default=0)),
                ('source', models.CharField(default='', max_length=40)),
                ('content_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recommend.article')),
            ],
            options={
                'unique_together': {('person_id', 'content_id', 'event_type')},
            },
        ),
    ]
