# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-12 08:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0023_auto_20180605_0827'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectstatus',
            options={'verbose_name_plural': 'project statuses'},
        ),
    ]
