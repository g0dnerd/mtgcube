# Generated by Django 5.0.6 on 2024-07-23 15:53

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("users", "0006_alter_user_pronouns"),
  ]

  operations = [
    migrations.AlterField(
      model_name="user",
      name="name",
      field=models.CharField(default="", max_length=255, verbose_name="Display Name"),
    ),
  ]
