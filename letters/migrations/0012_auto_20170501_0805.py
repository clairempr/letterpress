# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-01 08:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0011_auto_20170501_0804'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='documentsource',
            options={'ordering': ['name']},
        ),
    ]
