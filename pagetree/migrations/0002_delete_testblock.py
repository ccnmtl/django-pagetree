# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class ConditionalDeleteModel(migrations.DeleteModel):
    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        try:
            super(ConditionalDeleteModel, self).database_forwards(
                self, app_label, schema_editor, from_state, to_state)
        except:
            """ if it fails, it's totally fine. it just means that the
            table we wanted to delete doesn't exist. so we ignore it.

            it would be nice to catch a more specific exception, but
            different databases raise different ones..."""
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('pagetree', '0001_initial'),
    ]

    operations = [
        ConditionalDeleteModel(
            name='TestBlock',
        ),
    ]
