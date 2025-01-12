# Generated by Django 5.0.7 on 2024-08-06 14:49

from django.db import migrations, models


class Migration(migrations.Migration):
  dependencies = [
    ("users", "0008_remove_user_newly_created_remove_user_privacy_agreed_and_more"),
  ]

  operations = [
    migrations.AlterField(
      model_name="user",
      name="pronouns",
      field=models.CharField(
        choices=[("n", ""), ("m", "he/him"), ("f", "she/her"), ("x", "they/them")],
        default="n",
        max_length=1,
        verbose_name="My Pronouns",
      ),
    ),
  ]