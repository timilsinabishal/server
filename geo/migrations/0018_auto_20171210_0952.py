# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-10 09:52
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0017_auto_20171210_0947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminlevel',
            name='polygons',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, default=None, null=True, srid=4326),
        ),
    ]
