from django.utils import unittest
from pagetree.models import Hierarchy


class EmptyHierarchyTest(unittest.TestCase):
    """ a hierarchy with no sections in it
    (one Root gets created by default) """
    def setUp(self):
        self.h = Hierarchy.from_dict({'name' : "main",
                                      'base_url' : ""})

    def tearDown(self):
        self.h.delete()

    def test_easy(self):
        self.assertEqual(self.h.name, "main")

    def test_absolute_url(self):
        self.assertEqual(self.h.get_absolute_url(), "")

    def test_empty_hierarchy(self):
        self.assertEqual(self.h.get_root().hierarchy.id, self.h.id)

    def test_invalid_path(self):
        self.assertEqual(self.h.find_section_from_path("/foo/bar/baz/"),
                         None)

    def test_valid_path(self):
        self.assertEqual(self.h.find_section_from_path("/"),
                         self.h.get_root())

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

    def test_get_hierarchy(self):
        self.assertEqual(
            self.h.id,
            Hierarchy.get_hierarchy("main").id)

    def test_unicode(self):
        self.assertEqual(
            str(self.h),
            "main")
        self.assertEqual(
            unicode(self.h),
            "main")

    def test_empty_top_level(self):
        self.assertEqual(
            len(self.h.get_top_level()),
            0)


class OneLevelDeepTest(unittest.TestCase):
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict({
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
                })
        self.root.add_child_section_from_dict({
                'label': 'Section 2',
                'slug': 'section-2',
                'pageblocks': [],
                'children': [],
                })
        self.root.add_child_section_from_dict({
                'label': 'Section 3',
                'slug': 'section-3',
                'pageblocks': [],
                'children': [],
                })
        r = self.root.get_children()
        self.section1 = r[0]
        self.section2 = r[1]
        self.section3 = r[2]

    def tearDown(self):
        self.h.delete()

    def test_root(self):
        self.assertEqual(
            self.h.get_root().id,
            self.root.id)

    def test_children(self):
        self.assertEqual(
            self.section1.label,
            "Section 1")

    def test_valid_path(self):
        self.assertEqual(self.h.find_section_from_path("section-1/"),
                         self.section1)

    def test_trailing_slash_ignored(self):
        self.assertEqual(self.h.find_section_from_path("section-1/"),
                         self.h.find_section_from_path("section-1"))

    def test_get_first_leaf(self):
        self.assertEqual(self.h.get_first_leaf(self.root),
                         self.section1)

    def test_get_last_leaf(self):
        self.assertEqual(self.h.get_last_leaf(self.root),
                         self.section3)

    def test_get_module(self):
        self.assertEqual(
            self.root.get_module(),
            None)
        self.assertEqual(
            self.section1.get_module(),
            self.section1)

    def test_is_first_child(self):
        self.assertEqual(
            self.root.is_first_child(),
            True)
        self.assertEqual(
            self.section1.is_first_child(),
            True)
        self.assertEqual(
            self.section2.is_first_child(),
            False)

    def test_is_last_child(self):
        self.assertEqual(
            self.root.is_last_child(),
            True)
        self.assertEqual(
            self.section1.is_last_child(),
            False)
        self.assertEqual(
            self.section2.is_last_child(),
            False)
        self.assertEqual(
            self.section3.is_last_child(),
            True)

    def test_get_previous(self):
        self.assertEqual(
            self.section1.get_previous(),
            None)
        self.assertEqual(
            self.section2.get_previous(),
            self.section1)
        self.assertEqual(
            self.section3.get_previous(),
            self.section2)
        self.assertEqual(
            self.root.get_previous(),
            None)

    def test_get_next(self):
        self.assertEqual(
            self.section1.get_next(),
            self.section2)
        self.assertEqual(
            self.section2.get_next(),
            self.section3)
        self.assertEqual(
            self.section3.get_next(),
            None)
        self.assertEqual(
            self.root.get_previous(),
            None)

    def test_section_unicode(self):
        self.assertEqual(
            str(self.section1),
            "Section 1")

    def test_section_get_absolute_url(self):
        self.assertEqual(
            self.section1.get_absolute_url(),
            "section-1/")

    def test_section_get_first_leaf(self):
        self.assertEqual(
            self.section1.get_first_leaf(),
            self.section1)
        self.assertEqual(
            self.root.get_first_leaf(),
            self.section1)

    def test_section_get_last_leaf(self):
        self.assertEqual(
            self.section3.get_last_leaf(),
            self.section3)
        self.assertEqual(
            self.root.get_last_leaf(),
            self.section3)
        
