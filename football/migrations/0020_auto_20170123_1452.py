# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-23 14:52
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0019_auto_20170120_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='home_team',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='name', chained_model_field='name', on_delete=django.db.models.deletion.CASCADE, related_name='home_team', to='football.Division'),
        ),
    ]