# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-15 08:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0007_auto_20180124_1100'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ['order', '-created_at'], 'verbose_name_plural': 'entries'},
        ),
        migrations.AddField(
            model_name='entry',
            name='order',
            field=models.IntegerField(default=1),
        ),
    ]
