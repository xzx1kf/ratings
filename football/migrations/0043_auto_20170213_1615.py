# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-13 16:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0042_auto_20170213_1556'),
    ]

    operations = [
        migrations.CreateModel(
            name='Probability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('probability', models.FloatField(default=0)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Match')),
            ],
        ),
        migrations.CreateModel(
            name='Probability_Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='probabilities',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='probabilities',
            name='match',
        ),
        migrations.RemoveField(
            model_name='probabilities',
            name='team',
        ),
        migrations.DeleteModel(
            name='Probabilities',
        ),
        migrations.AddField(
            model_name='probability',
            name='probability_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Probability_Type'),
        ),
        migrations.AddField(
            model_name='probability',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Team'),
        ),
    ]
