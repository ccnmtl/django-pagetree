from __future__ import unicode_literals

from django.test import TestCase
from pagetree.forms import CloneHierarchyForm
from pagetree.tests.factories import HierarchyFactory


class CloneHierarchyFormTest(TestCase):
    def test_init(self):
        h = HierarchyFactory()
        CloneHierarchyForm(instance=h)

    def test_clean(self):
        h = HierarchyFactory()
        f = CloneHierarchyForm({
            'name': 'new name',
            'base_url': 'new',
        }, instance=h)
        self.assertTrue(f.is_valid())
        new_hier = f.save()
        self.assertEqual(new_hier.name, 'new name')
        self.assertEqual(new_hier.base_url, 'new')

    def test_clean_no_base_url(self):
        h = HierarchyFactory()
        f = CloneHierarchyForm({
            'name': 'new name',
            'base_url': '',
        }, instance=h)
        self.assertTrue(f.is_valid())
        new_hier = f.save()
        self.assertEqual(new_hier.name, 'new name')
        self.assertEqual(new_hier.base_url, 'new-name')

    def test_clean_prevents_duplicate_name(self):
        h = HierarchyFactory()
        f = CloneHierarchyForm({
            'name': h.name,
            'base_url': 'new',
        }, instance=h)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors, {
            '__all__': [
                u"There's already a hierarchy with the name: main"]
        })

    def test_clean_prevents_duplicate_base_url(self):
        h = HierarchyFactory()
        f = CloneHierarchyForm({
            'name': 'new name',
            'base_url': h.base_url,
        }, instance=h)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors, {
            '__all__': [
                u"There's already a hierarchy with the base_url: /pages/"]
        })
