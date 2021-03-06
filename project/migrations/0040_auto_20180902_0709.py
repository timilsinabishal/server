# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-02 07:09
from __future__ import unicode_literals

from django.db import migrations

from project.permissions import get_project_permissions_value


def update_assessment_permissions(apps, schema_editor):
    ProjectRole = apps.get_model('project', 'ProjectRole')

    admin_role = ProjectRole.objects.filter(is_creator_role=True)
    normal_role = ProjectRole.objects.filter(is_default_role=True)

    admin_role.update(
        assessment_permissions= get_project_permissions_value(
            'assessment', '__all__')
    )
    normal_role.update(
        assessment_permissions= get_project_permissions_value(
            'assessment', '__all__')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0039_projectrole_assessment_permissions'),
    ]

    operations = [
        migrations.RunPython(update_assessment_permissions)
    ]
