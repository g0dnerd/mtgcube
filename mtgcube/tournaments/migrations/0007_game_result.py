# Generated by Django 5.0.6 on 2024-07-03 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0006_remove_tournament_timer_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='result',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]