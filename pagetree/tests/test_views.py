from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from pagetree.models import Hierarchy, PageBlock


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
                     'css_extra': '',
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

    def test_edit_section(self):
        response = self.c.post(
            "/pagetree/edit_section/%d/" % self.section3.id,
            dict(label="new label"))
        self.assertEqual(response.status_code, 302)

    def test_reorder_section_children_empty(self):
        response = self.c.post(
            "/pagetree/reorder_section_children/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok")

    def test_reorder_section_children_get(self):
        response = self.c.get(
            "/pagetree/reorder_section_children/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.content, "only use POST for this")

    def test_reorder_pageblocks_empty(self):
        response = self.c.post(
            "/pagetree/reorder_pageblocks/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok")

    def test_reorder_pageblocks_get(self):
        response = self.c.get(
            "/pagetree/reorder_pageblocks/%d/" % self.section3.id,
            dict())
        self.assertEqual(response.content, "only use POST for this")

    def test_delete_pageblock(self):
        p = PageBlock.objects.all()[0]
        response = self.c.post("/pagetree/delete_pageblock/%d/" % p.id, dict())
        self.assertEqual(response.status_code, 302)

    def test_pageblock_json_export(self):
        p = PageBlock.objects.all()[0]
        response = self.c.get("/pagetree/pageblock/jsonexport/%d/" % p.id,
                              dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            '{"body": "You should now use the edit link to add content"}')

    def test_edit_pageblock(self):
        p = PageBlock.objects.all()[0]
        response = self.c.post("/pagetree/pageblock/edit/%d/" % p.id,
                               dict(body="new body text"))
        self.assertEqual(response.status_code, 302)
