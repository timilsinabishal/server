# Generated by Django 2.1.8 on 2019-05-24 08:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0025_analysisframeworkrole_is_private_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisframework',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True),
        ),
    ]