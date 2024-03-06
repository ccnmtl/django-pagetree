from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.encoding import smart_str
from django.test.client import Client
from pagetree.models import Hierarchy, PageBlock
from json import loads


class TestEditViews(TestCase):
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 2',
                'slug': 'section-2',
                'pageblocks': [
                    {'label': 'Welcome to your new Forest Site',
                     'css_extra': 'the-css-class',
                     'block_type': 'Test Block',
                     'body': 'You should now use the edit link to add content',
                     },
                ],
                'children': [],
            })
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 3',
                'slug': 'section-3',
                'pageblocks': [],
                'children': [],
            })
        r = self.root.get_children()
        self.section1 = r[0]
        self.section2 = r[1]
        self.section3 = r[2]
        self.u = User.objects.create(username="test")
        self.u.set_password("test")
        self.u.save()
        self.c = Client()
        self.c.login(username="test", password="test")

    def test_delete_section(self):
        response = self.c.post(
            "/pagetree/delete_section/%d/" % self.section3.id, dict())
        self.assertEqual(response.status_code, 302)

    def test_delete_section_get(self):
        response = self.c.get(
            "/pagetree/delete_section/%d/" % self.section3.id, dict())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_edit_section(self):
        response = self.c.post(
            "/pagetree/edit_section/%d/" % self.section3.id,
            dict(label="new label"))
        self.assertEqual(response.status_code, 302)

        self.section3.refresh_from_db()
        self.assertEqual(self.section3.label, 'new label')
        self.assertEqual(self.section3.slug, 'new-label')
        self.assertFalse(self.section3.show_toc)
        self.assertFalse(self.section3.deep_toc)

        response = self.c.post(
            "/pagetree/edit_section/%d/" % self.section3.id,
            dict(label="Longer Label", show_toc='on', deep_toc='True'))
        self.assertEqual(response.status_code, 302)

        self.section3.refresh_from_db()
        self.assertEqual(self.section3.label, 'Longer Label')
        self.assertEqual(self.section3.slug, 'longer-label')
        self.assertTrue(self.section3.show_toc)
        self.assertTrue(self.section3.deep_toc)

        response = self.c.post(
            "/pagetree/edit_section/%d/" % self.section3.id,
            dict(label="Longer Label", show_toc='False', deep_toc=False))
        self.assertEqual(response.status_code, 302)

        self.section3.refresh_from_db()
        self.assertEqual(self.section3.label, 'Longer Label')
        self.assertEqual(self.section3.slug, 'longer-label')
        self.assertFalse(self.section3.show_toc)
        self.assertFalse(self.section3.deep_toc)

    def test_add_child_section(self):
        response = self.c.post(
            "/pagetree/section/add/%d/" % self.section3.id,
            dict(label="new label"))
        self.assertEqual(response.status_code, 302)

    def test_move_section(self):
        response = self.c.post(
            "/pagetree/section/move/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(smart_str(response.content),
                         "could not move section")

    def test_move_section_get(self):
        response = self.c.get(
            "/pagetree/section/move/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(smart_str(response.content),
                         "only use POST for this")

    def test_add_pageblock(self):
        response = self.c.post(
            "/pagetree/pageblock/add/%d/" % self.section3.id,
            dict(blocktype="Test Block", body="some text"))
        self.assertEqual(response.status_code, 302)

    def test_reorder_section_children_empty(self):
        response = self.c.post(
            "/pagetree/reorder_section_children/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(smart_str(response.content), "ok")

    def test_reorder_section_children_get(self):
        response = self.c.get(
            "/pagetree/reorder_section_children/%d/" % self.section3.id,
            dict())
        self.assertEqual(smart_str(response.content),
                         "only use POST for this")

    def test_reorder_pageblocks_empty(self):
        response = self.c.post(
            "/pagetree/reorder_pageblocks/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(smart_str(response.content), "ok")

    def test_reorder_pageblocks_get(self):
        response = self.c.get(
            "/pagetree/reorder_pageblocks/%d/" % self.section3.id,
            dict())
        self.assertEqual(smart_str(response.content),
                         "only use POST for this")

    def test_delete_pageblock(self):
        p = PageBlock.objects.all()[0]
        response = self.c.post("/pagetree/delete_pageblock/%d/" % p.id, dict())
        self.assertEqual(response.status_code, 302)

    def test_pageblock_json_export(self):
        p = PageBlock.objects.all()[0]

        response = self.c.get("/pagetree/pageblock/jsonexport/%d/" % p.id,
                              dict())
        self.assertEqual(response.status_code, 200)

        the_json = loads(smart_str(response.content))
        self.assertEqual(the_json["body"],
                         "You should now use the edit link to add content")
        self.assertEqual(the_json["css_extra"], "the-css-class")
        self.assertEqual(the_json["block_type"], "Test Block")
        self.assertEqual(the_json["label"], "Welcome to your new Forest Site")

    def test_edit_pageblock(self):
        p = PageBlock.objects.all()[0]
        response = self.c.post("/pagetree/pageblock/edit/%d/" % p.id,
                               dict(body="new body text"))
        self.assertEqual(response.status_code, 302)

    def test_exporter(self):
        response = self.c.get("/pagetree/export/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

    def test_create_tree_root(self):
        response = self.c.get("/pagetree/create_tree_root",
                              {}, HTTP_REFERER='http://foo/bar')
        self.assertEqual(response.status_code, 302)
