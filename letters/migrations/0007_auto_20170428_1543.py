# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-28 15:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0006_auto_20170428_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='envelope',
            name='language',
            field=models.CharField(blank=True, default='EN', max_length=2),
        ),
        migrations.AddField(
            model_name='miscdocument',
            name='language',
            field=models.CharField(blank=True, default='EN', max_length=2),
        ),
    ]
