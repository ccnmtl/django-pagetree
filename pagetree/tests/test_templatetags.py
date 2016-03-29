from __future__ import unicode_literals

from django.test import TestCase
from pagetree.tests.factories import RootSectionFactory, UserFactory

from pagetree.templatetags.user_status import is_section_unlocked


class IsSectionUnlockedTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.section = RootSectionFactory()

    def test_is_section_unlocked_empty_section(self):
        self.assertEqual(
            is_section_unlocked(self.section, self.user), '1')
