# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-02 12:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0033_auto_20170201_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='record',
            field=models.CharField(default='', max_length=10),
        ),
    ]
