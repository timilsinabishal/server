# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-15 08:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0032_auto_20180815_0825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectjoinrequest',
            name='role',
        ),
        migrations.RemoveField(
            model_name='projectmembership',
            name='role',
        ),
    ]
