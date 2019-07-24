# Generated by Django 2.1.8 on 2019-06-26 06:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0018_auto_20190624_1017'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featureaccess',
            name='email_domains',
        ),
        migrations.RemoveField(
            model_name='featureaccess',
            name='feature',
        ),
        migrations.RemoveField(
            model_name='featureaccess',
            name='users',
        ),
        migrations.AddField(
            model_name='feature',
            name='email_domains',
            field=models.ManyToManyField(blank=True, to='user.EmailDomain'),
        ),
        migrations.AddField(
            model_name='feature',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='feature',
            name='key',
            field=models.CharField(choices=[('private_project', 'Private projects'), ('tabular', 'Tabular'), ('zoomable_image', 'Zoomable image')], max_length=255, unique=True),
        ),
        migrations.DeleteModel(
            name='FeatureAccess',
        ),
    ]