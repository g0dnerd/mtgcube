# Generated by Django 5.0.7 on 2024-08-07 09:48

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("tournaments", "0044_image_draft_id_to_foreign_key"),
  ]

  operations = [
    migrations.AddField(
      model_name="draft",
      name="first_table",
      field=models.IntegerField(default=0),
    ),
    migrations.AddField(
      model_name="draft",
      name="last_table",
      field=models.IntegerField(default=0),
    ),
  ]