# Generated by Django 5.0.7 on 2024-08-01 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0041_tournament_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='dropped',
            field=models.BooleanField(default=False),
        ),
    ]
