# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-10 06:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='url',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='organizationtype',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
