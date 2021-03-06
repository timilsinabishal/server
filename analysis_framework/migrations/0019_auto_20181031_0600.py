# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-31 06:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0018_analysisframework_client_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='filter_type',
            field=models.CharField(choices=[('number', 'Number'), ('list', 'List'), ('intersects', 'Intersection between two numbers')], default='list', max_length=20),
        ),
    ]
