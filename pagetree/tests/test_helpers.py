from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from pagetree.helpers import get_hierarchy, get_section_from_path
from pagetree.helpers import block_submitted
from pagetree.models import Hierarchy


class TestGetHierarchy(TestCase):
    def test_empty(self):
        self.assertEqual(Hierarchy.objects.count(), 0)
        get_hierarchy()
        self.assertEqual(Hierarchy.objects.count(), 1)

    def test_idempotent(self):
        self.assertEqual(Hierarchy.objects.count(), 0)
        get_hierarchy()
        self.assertEqual(Hierarchy.objects.count(), 1)
        get_hierarchy()
        self.assertEqual(Hierarchy.objects.count(), 1)

    def test_default_args(self):
        h = get_hierarchy()
        self.assertEqual(h.name, "main")
        self.assertEqual(h.base_url, "/")

    def test_dont_care_about_type(self):
        h = get_hierarchy()
        h2 = get_hierarchy(h)
        self.assertEqual(h.id, h2.id)


class TestGetSectionFromPath(TestCase):
    def test_empty(self):
        s = get_section_from_path("/")
        self.assertEqual(s.hierarchy.name, "main")


class StubBlockNoSubmit(object):
    pass


class StubBlockSubmit(object):
    def __init__(self, submit_value=False, unlocked_value=False):
        self.submit_value = submit_value
        self.unlocked_value = unlocked_value

    def needs_submit(self):
        return self.submit_value

    def unlocked(self, u):
        return self.unlocked_value


class TestBlockSubmitted(TestCase):
    def test_anonymous(self):
        u = AnonymousUser()
        self.assertFalse(block_submitted(None, u))

    def test_no_submit(self):
        u = User.objects.create(username="test")
        b = StubBlockNoSubmit()
        self.assertTrue(block_submitted(b, u))

    def test_submit_returns_false(self):
        u = User.objects.create(username="test")
        b = StubBlockSubmit(submit_value=False)
        self.assertTrue(block_submitted(b, u))

    def test_submit_unlocked(self):
        u = User.objects.create(username="test")
        b = StubBlockSubmit(submit_value=True, unlocked_value=True)
        self.assertTrue(block_submitted(b, u))

    def test_submit_locked(self):
        u = User.objects.create(username="test")
        b = StubBlockSubmit(submit_value=True, unlocked_value=False)
        self.assertFalse(block_submitted(b, u))
