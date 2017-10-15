# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-16 10:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0005_auto_20171013_1259'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lead',
            name='attachment',
        ),
        migrations.AddField(
            model_name='lead',
            name='attachment',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='gallery.File'),
        ),
    ]