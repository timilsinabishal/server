# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-31 06:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0014_auto_20181031_0600'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filterdata',
            old_name='number_from',
            new_name='from_number',
        ),
        migrations.RenameField(
            model_name='filterdata',
            old_name='number_to',
            new_name='to_number',
        ),
    ]
