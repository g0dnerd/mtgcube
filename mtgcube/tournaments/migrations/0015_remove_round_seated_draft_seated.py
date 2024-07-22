# Generated by Django 5.0.6 on 2024-07-18 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0014_remove_draft_seated_round_seated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='round',
            name='seated',
        ),
        migrations.AddField(
            model_name='draft',
            name='seated',
            field=models.BooleanField(default=False),
        ),
    ]
