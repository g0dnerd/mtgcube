# Generated by Django 5.0.6 on 2024-07-04 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0007_game_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='result_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]