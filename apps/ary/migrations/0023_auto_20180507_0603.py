# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-07 06:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ary', '0022_scorebucket'),
    ]

    operations = [
        migrations.AddField(
            model_name='metadatafield',
            name='tooltip',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='methodologyfield',
            name='tooltip',
            field=models.TextField(blank=True),
        ),
    ]