# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-06 12:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lang', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='link',
            name='link_collection',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='links', to='lang.LinkCollection'),
            preserve_default=False,
        ),
    ]