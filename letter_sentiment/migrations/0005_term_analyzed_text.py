# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-01 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letter_sentiment', '0004_auto_20170530_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='term',
            name='analyzed_text',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
