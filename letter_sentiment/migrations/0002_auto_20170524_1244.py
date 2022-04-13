# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-24 10:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('letter_sentiment', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='term',
            options={'ordering': ('text',)},
        ),
        migrations.AlterField(
            model_name='term',
            name='custom_sentiment',
            field=models.ForeignKey(on_delete=models.CASCADE, to='letter_sentiment.CustomSentiment'),
        ),
    ]
