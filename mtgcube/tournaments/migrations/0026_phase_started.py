# Generated by Django 5.0.7 on 2024-07-26 15:42

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("tournaments", "0025_remove_phase_current_round_phase_finished"),
  ]

  operations = [
    migrations.AddField(
      model_name="phase",
      name="started",
      field=models.BooleanField(default=False),
    ),
  ]
