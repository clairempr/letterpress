# Generated by Django 4.0.10 on 2023-12-14 00:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0016_auto_20220531_0130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='envelope',
            name='writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(model_name)s_writer', to='letters.correspondent'),
        ),
        migrations.AlterField(
            model_name='letter',
            name='writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(model_name)s_writer', to='letters.correspondent'),
        ),
        migrations.AlterField(
            model_name='miscdocument',
            name='envelopes',
            field=models.ManyToManyField(blank=True, to='letters.envelope'),
        ),
        migrations.AlterField(
            model_name='miscdocument',
            name='images',
            field=models.ManyToManyField(blank=True, to='letters.documentimage'),
        ),
        migrations.AlterField(
            model_name='miscdocument',
            name='place',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='letters.place'),
        ),
        migrations.AlterField(
            model_name='miscdocument',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='letters.documentsource'),
        ),
        migrations.AlterField(
            model_name='miscdocument',
            name='writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(model_name)s_writer', to='letters.correspondent'),
        ),
    ]