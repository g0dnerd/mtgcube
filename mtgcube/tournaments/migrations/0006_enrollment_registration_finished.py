# Generated by Django 5.0.6 on 2024-07-15 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0005_tournament_announcement'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='registration_finished',
            field=models.BooleanField(default=False),
        ),
    ]