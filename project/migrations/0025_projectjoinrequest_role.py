# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-06 10:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0024_auto_20180612_0859'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectjoinrequest',
            name='role',
            field=models.CharField(choices=[('normal', 'Normal'), ('admin', 'Admin')], default='normal', max_length=96),
        ),
    ]
