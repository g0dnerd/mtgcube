# Generated by Django 5.0.7 on 2024-07-27 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0027_draft_slug_tournament_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='current_round',
            field=models.IntegerField(default=0),
        ),
    ]