# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-04 07:32
from __future__ import unicode_literals

from django.db import migrations


def migrate_added_by(apps, schema_editor):
    Project = apps.get_model('project', 'Project')
    ProjectMembership = apps.get_model('project', 'ProjectMembership')
    for project in Project.objects.all():
        admin_ship = ProjectMembership.objects.filter(
            project=project,
            role='admin'
        ).first()
        if admin_ship:
            admin = admin_ship.member
            for member in ProjectMembership.objects.filter(project=project):
                member.added_by = admin
                member.save()


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0019_projectmembership_added_by'),
    ]

    operations = [
        migrations.RunPython(migrate_added_by),
    ]