# Generated by Django 5.0.6 on 2024-07-10 09:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0011_draft'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tournament',
            name='is_event',
        ),
        migrations.RemoveField(
            model_name='tournament',
            name='round_length',
        ),
        migrations.RemoveField(
            model_name='tournament',
            name='round_timer_start',
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('phase_idx', models.IntegerField(default=0)),
                ('round_number', models.IntegerField(default=3)),
                ('current_round', models.IntegerField(default=0)),
                ('round_length', models.IntegerField(default=50)),
                ('round_timer_start', models.DateTimeField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournaments.tournament')),
            ],
        ),
        migrations.DeleteModel(
            name='Draft',
        ),
    ]