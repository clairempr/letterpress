# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-08 10:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0012_auto_20170501_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentimage',
            name='type',
            field=models.CharField(choices=[('L', 'Letter'), ('E', 'Envelope'), ('T', 'Transcription'), ('D', 'Other')], max_length=1),
        ),
    ]
