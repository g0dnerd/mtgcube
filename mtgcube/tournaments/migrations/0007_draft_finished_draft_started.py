# Generated by Django 5.0.6 on 2024-07-15 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0006_enrollment_registration_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='draft',
            name='finished',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='draft',
            name='started',
            field=models.BooleanField(default=False),
        ),
    ]