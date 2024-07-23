# Generated by Django 5.0.6 on 2024-07-23 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_name_alter_user_pronouns'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='newly_created',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='privacy_agreed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='tos_agreed',
            field=models.BooleanField(default=False),
        ),
    ]