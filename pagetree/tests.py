from django.utils import unittest
from pagetree.models import Hierarchy, PageBlock


class EmptyHierarchyTest(unittest.TestCase):
    """ a hierarchy with no sections in it
    (one Root gets created by default) """
    def setUp(self):
        self.h = Hierarchy.from_dict({'name': "main",
                                      'base_url': ""})

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


class OneLevelWithBlocksTest(unittest.TestCase):
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict({
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Text Block',
                     'body': 'some body text section 1 block 1',
                     },
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Text Block',
                     'body': 'some body text section 1 block 2',
                     }
                    ],
                'children': [],
                })
        r = self.root.get_children()
        self.section1 = r[0]

    def tearDown(self):
        self.h.delete()

    def test_render(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            b.render().strip(),
            "<p>some body text section 1 block 1</p>")

    def test_render_js(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            b.render_js().strip(),
            "")

    def test_render_css(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            b.render_css().strip(),
            "")

    def test_render_summary(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            b.render_summary().strip(),
            "some body text section 1 block 1")

    def test_edit_form(self):
        b = self.section1.pageblock_set.all()[0]
        f = b.edit_form()
        self.assertEqual(
            "body" in f.fields,
            True)

    def test_default_edit_form(self):
        b = self.section1.pageblock_set.all()[0]
        f = b.default_edit_form()
        self.assertEqual(
            "label" in f.fields,
            True)
        self.assertEqual(
            "css_extra" in f.fields,
            True)

    def test_edit(self):
        b = self.section1.pageblock_set.all()[0]
        b.edit(dict(label="new label",
                    css_extra="new css_extra",
                    body="new_body"), None)
        self.assertEqual(b.label, "new label")
        self.assertEqual(b.css_extra, "new css_extra")
        self.assertEqual(b.block().body, "new_body")

    def test_serialization(self):
        self.assertEqual(
            self.section1.as_dict()['pageblocks'][0]['body'],
            'some body text section 1 block 1')

    def test_delete_block(self):
        block1 = self.section1.pageblock_set.all()[0]
        block2 = self.section1.pageblock_set.all()[1]
        block1.delete()
        # block2 should now be #1, but we need to re-fetch it
        block2 = PageBlock.objects.get(id=block2.id)
        self.assertEqual(block2.ordinality, 1)
