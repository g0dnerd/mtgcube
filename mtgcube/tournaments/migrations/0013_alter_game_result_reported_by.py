# Generated by Django 5.0.6 on 2024-07-18 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0012_round_paired_alter_image_draft_idx'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='result_reported_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
