# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-23 15:21
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0028_auto_20170123_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='away_team',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='division', chained_model_field='division', on_delete=django.db.models.deletion.CASCADE, related_name='away_team', to='football.Team'),
        ),
    ]