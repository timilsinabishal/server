# Generated by Django 2.1.8 on 2019-04-29 05:41

from django.db import migrations


def clear_admin_level_geo_area_cache(apps, schema_editor):
    AdminLevel = apps.get_model('geo', 'AdminLevel')

    AdminLevel.objects.all().update(geo_area_titles=None)


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0032_merge_20181212_0553'),
    ]

    operations = [
        migrations.RunPython(clear_admin_level_geo_area_cache),
    ]