# Generated by Django 5.0.6 on 2024-07-15 08:20

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("tournaments", "0001_initial"),
  ]

  operations = [
    migrations.AddField(
      model_name="enrollment",
      name="seat",
      field=models.IntegerField(default=0),
    ),
  ]
