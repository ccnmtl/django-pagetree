# flake8: noqa
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hierarchy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('base_url', models.CharField(default=b'', max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinality', models.PositiveIntegerField(default=1)),
                ('label', models.CharField(max_length=256, null=True, blank=True)),
                ('css_extra', models.CharField(help_text=b'extra CSS classes (space separated)', max_length=256, null=True, blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('section', 'ordinality'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('label', models.CharField(max_length=256)),
                ('slug', models.SlugField()),
                ('show_toc', models.BooleanField(default=False, help_text=b'list table of contents of immediate child sections (if applicable)')),
                ('deep_toc', models.BooleanField(default=False, help_text=b'include children of children in TOC. (this only makes sense if the above is checked)')),
                ('hierarchy', models.ForeignKey(to='pagetree.Hierarchy', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(default=b'/', max_length=256)),
                ('hierarchy', models.ForeignKey(to='pagetree.Hierarchy', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPageVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'incomplete', max_length=256)),
                ('first_visit', models.DateTimeField(auto_now_add=True)),
                ('last_visit', models.DateTimeField(auto_now=True)),
                ('section', models.ForeignKey(to='pagetree.Section', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('activity', models.TextField(default=b'', null=True, blank=True)),
                ('data', models.TextField(default=b'', null=True, blank=True)),
                ('comment', models.TextField(default=b'', null=True, blank=True)),
                ('section', models.ForeignKey(to='pagetree.Section', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-saved_at'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userpagevisit',
            unique_together=set([('user', 'section')]),
        ),
        migrations.AlterUniqueTogether(
            name='userlocation',
            unique_together=set([('user', 'hierarchy')]),
        ),
        migrations.AddField(
            model_name='pageblock',
            name='section',
            field=models.ForeignKey(to='pagetree.Section', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
