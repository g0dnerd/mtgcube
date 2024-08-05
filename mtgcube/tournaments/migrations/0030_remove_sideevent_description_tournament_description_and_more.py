# Generated by Django 5.0.7 on 2024-07-30 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0029_alter_draft_slug_alter_tournament_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sideevent',
            name='description',
        ),
        migrations.AddField(
            model_name='tournament',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='tournament',
            name='format_description',
            field=models.TextField(blank=True),
        ),
    ]
