# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-23 14:57
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0022_auto_20170123_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='home_team',
            field=smart_selects.db_fields.GroupedForeignKey(group_field='name', on_delete=django.db.models.deletion.CASCADE, related_name='home_team', to='football.Division'),
        ),
    ]
