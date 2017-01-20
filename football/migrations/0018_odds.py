# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-19 14:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0017_auto_20170118_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='Odds',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home', models.FloatField(default=0)),
                ('draw', models.FloatField(default=0)),
                ('away', models.FloatField(default=0)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Match')),
            ],
            options={
                'verbose_name_plural': 'Odds',
            },
        ),
    ]