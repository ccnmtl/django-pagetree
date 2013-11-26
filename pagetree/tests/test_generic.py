from django.test import TestCase
from pagetree.models import Hierarchy
from pagetree.generic.views import has_responses, visit_root


class OneLevelDeepTest(TestCase):
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
                'pageblocks': [],
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

    def tearDown(self):
        self.h.delete()

    def test_has_responses(self):
        self.assertFalse(has_responses(self.section1))

    def test_visit_root(self):
        r = visit_root(self.section1)
        self.assertEqual(r.status_code, 302)

    def test_visit_root_fallback(self):
        r = visit_root(self.section3)
        self.assertEqual(r.status_code, 302)
