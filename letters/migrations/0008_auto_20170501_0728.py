# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-01 07:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0007_auto_20170428_1543'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='correspondent',
            options={'ordering': ['__str__']},
        ),
    ]
