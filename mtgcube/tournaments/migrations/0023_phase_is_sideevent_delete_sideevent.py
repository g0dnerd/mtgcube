# Generated by Django 5.0.7 on 2024-07-26 11:27

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("tournaments", "0022_sideevent"),
  ]

  operations = [
    migrations.AddField(
      model_name="phase",
      name="is_sideevent",
      field=models.BooleanField(default=False),
    ),
    migrations.DeleteModel(
      name="SideEvent",
    ),
  ]
