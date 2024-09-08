# Generated by Django 5.0.7 on 2024-08-06 15:05

from django.db import migrations

def populate_draft_foreign_key(apps, schema_editor):
    Image = apps.get_model('tournaments', 'Image')
    Draft = apps.get_model('tournaments', 'Draft')

    for image in Image.objects.all():
        if image.draft_idx is not None:
            try:
                draft = Draft.objects.get(id=image.draft_idx)
                image.draft = draft
                image.save()
            except Draft.DoesNotExist:
                pass  # Handle if there are invalid draft_idx values that do not match any Draft

class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0043_image_draft'),
    ]

    operations = [
        migrations.RunPython(populate_draft_foreign_key),
    ]
