# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-25 09:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oauth', '0002_oauthqquser_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='OAuthWeiboUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('access_token', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='access_token')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'db_table': 'tb_oauth_weibo',
                'verbose_name_plural': 'Weibo登录用户数据',
                'verbose_name': 'Weibo登录用户数据',
            },
        ),
    ]
