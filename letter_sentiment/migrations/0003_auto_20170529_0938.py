# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-29 09:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('letter_sentiment', '0002_auto_20170524_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='term',
            name='weight',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='term',
            name='custom_sentiment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='term', to='letter_sentiment.CustomSentiment'),
        ),
    ]
