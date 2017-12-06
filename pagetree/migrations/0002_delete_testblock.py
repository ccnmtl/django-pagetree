# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
from django.db import (
    migrations,
    DatabaseError, OperationalError, ProgrammingError
)


class ConditionalDeleteModel(migrations.DeleteModel):
    def database_forwards(
            self, app_label, schema_editor, from_state, to_state):
        # The tests use this model
        if 'runtests.py' in sys.argv or 'test' in sys.argv or \
           'jenkins' in sys.argv:
            return

        try:
            super(ConditionalDeleteModel, self).database_forwards(
                app_label, schema_editor, from_state, to_state)
        except (DatabaseError, OperationalError, ProgrammingError):
            """ if it fails, it's totally fine. it just means that the
            table we wanted to delete doesn't exist. so we ignore it.
            """
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
