# Generated by Django 5.0.6 on 2024-07-23 10:15

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("tournaments", "0019_remove_player_name"),
  ]

  operations = [
    migrations.AddField(
      model_name="player",
      name="name",
      field=models.CharField(default="", max_length=50),
    ),
  ]
