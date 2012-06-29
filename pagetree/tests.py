from django.utils import unittest
from pagetree.models import Hierarchy


class EmptyHierarchyTest(unittest.TestCase):
    """ a hierarchy with no sections in it
    (one Root gets created by default) """
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")

    def test_easy(self):
        self.assertEqual(self.h.name, "main")

    def test_absolute_url(self):
        self.assertEqual(self.h.get_absolute_url(), "")

    def test_empty_hierarchy(self):
        self.assertEqual(self.h.get_root().hierarchy.id, self.h.id)

    def test_invalid_path(self):
        self.assertEqual(self.h.find_section_from_path("/foo/bar/baz"),
                         None)

    def test_get_first_leaf(self):
        self.assertEqual(
            self.h.get_first_leaf(self.h.get_root()).id,
            self.h.get_root().id)

    def test_get_last_leaf(self):
        self.assertEqual(
            self.h.get_last_leaf(self.h.get_root()).id,
            self.h.get_root().id)

    def test_as_dict(self):
        self.assertEqual(
            'name' in self.h.as_dict(),
            True)
        self.assertEqual(
            'base_url' in self.h.as_dict(),
            True)
        self.assertEqual(
            'sections' in self.h.as_dict(),
            True)
