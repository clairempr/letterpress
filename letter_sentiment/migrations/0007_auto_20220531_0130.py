# Generated by Django 3.2.13 on 2022-05-31 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letter_sentiment', '0006_customsentiment_max_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customsentiment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='term',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
