# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-01 07:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0009_auto_20170501_0744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='place',
            options={'ordering': ['name', 'state']},
        ),
    ]
