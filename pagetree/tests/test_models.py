from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User
from django.http import Http404
from django.utils.encoding import smart_str
import django.db
from django.db import transaction

from pagetree.models import Hierarchy, PageBlock, UserPageVisit
from pagetree.test_models import TestBlock
from pagetree.tests.factories import (
    RootSectionFactory, TestBlockFactory, UserFactory, UserPageVisitFactory,
    HierarchyFactory
)


class UserTest(TestCase):
    def setUp(self):
        self.u = UserFactory()

    def test_is_valid_from_factory(self):
        self.u.full_clean()


class HierarchyTest(TestCase):
    def setUp(self):
        self.h = HierarchyFactory()

    def test_is_valid_from_factory(self):
        self.h.full_clean()


class RootSectionTest(TestCase):
    def setUp(self):
        self.s = RootSectionFactory()

    def test_is_valid_from_factory(self):
        self.s.full_clean()


class EmptyHierarchyTest(TestCase):
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

    def test_get_section_from_path(self):
        self.assertEqual(self.h.get_section_from_path("/"),
                         self.h.get_root())

    def test_get_section_from_path_invalid(self):
        with self.assertRaises(Http404):
            self.h.get_section_from_path("/foo/bar/baz")

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

    def test_str(self):
        self.assertEqual(smart_str(self.h), "main")

    def test_empty_top_level(self):
        self.assertEqual(
            len(self.h.get_top_level()),
            0)

    def test_available_pageblocks_empty(self):
        with self.settings(PAGEBLOCKS=None):
            self.assertEqual(self.h.available_pageblocks(), [])

    def test_add_section_from_dict(self):
        s = self.h.add_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [
                    {
                        'label': 'Section 2',
                        'slug': 'section-2',
                        'pageblocks': [],
                        'children': [],
                    }],
            })
        # adding straight to the hierarchy needs to
        # create a Root section, not a regular one
        self.assertEqual(s.label, 'Root')
        self.assertEqual(s.slug, '')


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

    def test_root(self):
        self.assertEqual(
            self.h.get_root().id,
            self.root.id)

    def test_children(self):
        self.assertEqual(
            self.section1.label,
            "Section 1")

    def test_add_child_form(self):
        f = self.section1.add_child_section_form()
        self.assertEqual(
            'label' in f.fields,
            True)

    def test_edit_form(self):
        f = self.section1.edit_form()
        self.assertEqual(
            'label' in f.fields,
            True)
        self.assertEqual(
            'slug' in f.fields,
            True)

    def test_get_path(self):
        self.assertEqual(
            self.section1.get_path(),
            "section-1/")

    def test_add_pageblock_form(self):
        f = self.section1.add_pageblock_form()
        self.assertEqual(
            'label' in f.fields,
            True)
        self.assertEqual(
            'css_extra' in f.fields,
            True)
        self.assertFalse(f.fields['label'].required)
        self.assertFalse(f.fields['css_extra'].required)

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

    def test_section_str(self):
        self.assertEqual(
            smart_str(self.section1),
            "Section 1")

    def test_section_get_absolute_url(self):
        self.assertEqual(
            self.section1.get_absolute_url(),
            "section-1/")

    def test_section_get_edit_url(self):
        self.assertEqual(
            self.section1.get_edit_url(),
            "edit/section-1/")

    def test_section_get_instructor_url(self):
        self.assertEqual(
            self.section1.get_instructor_url(),
            "instructor/section-1/")

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

    def test_update_children_order(self):
        normal_order = [
            self.section1.id,
            self.section2.id,
            self.section3.id]
        normal_order.reverse()
        self.root.update_children_order(normal_order)
        r = self.root.get_children()
        self.assertEqual([s.id for s in r], normal_order)

    def test_get_tree_depth(self):
        self.assertEqual(self.section1.get_tree_depth(), 1)
        self.assertEqual(self.section2.get_tree_depth(), 2)
        self.assertEqual(self.section3.get_tree_depth(), 3)


class OneLevelWithBlocksTest(TestCase):
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Test Block',
                     'body': 'some body text section 1 block 1',
                     },
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Test Block',
                     'body': 'some body text section 1 block 2',
                     }
                ],
                'children': [],
            })
        r = self.root.get_children()
        self.section1 = r[0]

    def tearDown(self):
        self.h.delete()

    def test_str(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            smart_str(b),
            "Section 1 [1]: ")

    def test_edit_label(self):
        b = self.section1.pageblock_set.all()[0]
        self.assertEqual(
            b.edit_label(), 'Test Block')

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
        self.assertFalse(f.fields['label'].required)
        self.assertFalse(f.fields['css_extra'].required)

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

    def test_closing_children(self):
        self.assertEqual(
            list(self.section1.closing_children()),
            [self.section1])

    def test_move_form(self):
        f = self.section1.move_form()
        self.assertTrue(f is not None)

    def test_update_pageblocks_order(self):
        normal_order = [p.id for p in self.section1.pageblock_set.all()]
        normal_order.reverse()
        self.section1.update_pageblocks_order(normal_order)
        self.assertEqual(
            [p.id for p in self.section1.pageblock_set.all()],
            normal_order)

    def test_import_from_dict(self):
        b = self.section1.pageblock_set.first()
        d = {'label': 'new label',
             'css_extra': 'new css_extra',
             'body': 'new body'}
        b.import_from_dict(d)
        self.assertEqual(b.label, 'new label')
        self.assertEqual(b.css_extra, 'new css_extra')

        sub = b.block()
        self.assertEqual(sub.body, 'new body')

    def test_import_custom_block_dict(self):
        b = self.section1.pageblock_set.first()
        d = {
            'block_type': 'Test Block',
            'body': 'abc',
        }
        b.import_from_dict(d)

        sub = b.block()
        self.assertEqual(sub.display_name, 'Test Block')
        self.assertEqual(sub.body, 'abc')


class UserTrackingTest(TestCase):
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

        self.h2 = Hierarchy.objects.create(name="other", base_url="")
        self.h2.get_root().add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })
        self.h2.get_root().add_child_section_from_dict(
            {
                'label': 'Section 2',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

        self.user = User.objects.create(username='testuser')

    def tearDown(self):
        self.h.delete()
        self.h2.delete()
        self.user.delete()

    def test_user_visit(self):
        self.h.user_visit(self.user, self.section1)
        self.assertEqual(
            self.h.get_user_location(self.user),
            "section-1/"
        )
        self.assertEqual(
            self.h.get_user_section(self.user),
            self.section1
        )

    def test_user_visit_section(self):
        self.section1.user_visit(self.user)
        self.assertEqual(
            self.h.get_user_location(self.user),
            "section-1/"
        )
        self.assertEqual(
            self.h.get_user_section(self.user),
            self.section1
        )

    def test_user_pagevisit(self):
        self.assertEqual(
            self.section1.get_uservisit(self.user),
            None
        )
        self.section1.user_pagevisit(self.user, status="incomplete")
        self.assertEqual(
            self.section1.get_uservisit(self.user).status,
            "incomplete"
        )
        self.section1.user_pagevisit(self.user, status="complete")
        self.assertEqual(
            self.section1.get_uservisit(self.user).status,
            "complete"
        )

    def test_user_pagevisit_multiple(self):
        self.section1.user_pagevisit(self.user, status="complete")
        try:
            with transaction.atomic():
                # then stuff another one in manually to simulate a
                # race condition
                UserPageVisit.objects.create(section=self.section1,
                                             user=self.user,
                                             status="bad status")
                # should not be able to happen
                self.assertEqual(True, False)
        except django.db.IntegrityError:
            self.assertEqual(True, True)
        self.section1.user_pagevisit(self.user, status="complete")

    def test_gate_check(self):
        self.assertEqual(self.section1.gate_check(None),
                         (False, self.section1))
        self.assertEqual(self.section1.gate_check(self.user), (True, None))
        self.assertEqual(self.section2.gate_check(self.user),
                         (False, self.section1))
        self.section1.user_pagevisit(self.user, status="complete")
        self.section2.user_pagevisit(self.user, status="complete")
        self.section3.user_pagevisit(self.user, status="complete")
        self.assertEqual(self.section1.gate_check(self.user), (True, None))

    def test_gate_check_multiple_hierarchies(self):
        children = self.h2.get_root().get_children()

        # first section of any hierarchu returns "True" from gate_check
        self.assertEqual(
            children[0].gate_check(self.user), (True, None))
        self.assertEqual(
            children[1].gate_check(self.user), (False, children[0]))


class VersionTest(TestCase):
    def setUp(self):
        self.h = Hierarchy.objects.create(name="main", base_url="")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Test Block',
                     'body': 'some body text section 1 block 1',
                     },
                    {'label': '',
                     'css_extra': '',
                     'block_type': 'Test Block',
                     'body': 'some body text section 1 block 2',
                     }
                ],
                'children': [
                    {
                        'label': 'Child 1',
                        'slug': 'child-1',
                        'pageblocks': [],
                        'children': [{
                                'label': 'GrandChild 1',
                                'slug': 'grandchild-1',
                                'pageblocks': [],
                                'children': [],
                        }],
                    }
                ],
            })
        r = self.root.get_children()
        self.section1 = r[0]
        self.user = User.objects.create(username='testuser')

    def tearDown(self):
        self.h.delete()
        self.user.delete()

    def test_save_version(self):
        self.assertEqual(
            self.section1.version_set.count(),
            0)
        self.section1.save_version(self.user, activity="test save")
        self.assertEqual(
            self.section1.version_set.count(),
            1)
        v = self.section1.version_set.all()[0]
        self.assertEqual(
            v.activity, "test save")
        self.assertEqual(
            v.user, self.user)
        # just some quick checks that our block bodies made it into
        # the data
        self.assertEqual(
            "some body text section 1 block 1" in v.data,
            True)
        self.assertEqual(
            "some body text section 1 block 2" in v.data,
            True)
        # and make sure the entire subtree got serialized
        self.assertEqual(
            'GrandChild 1' in v.data,
            True)

    def test_more_recent_versions(self):
        self.section1.save_version(self.user, activity="test save")
        # grab the most recent version
        v = list(self.section1.version_set.all())[-1]
        # should not be any newer ones
        self.assertEqual(
            len(v.more_recent_versions()),
            0)
        # add another
        self.section1.save_version(self.user, activity="another test save")
        # now there should be
        self.assertEqual(
            len(v.more_recent_versions()),
            1)

    def test_more_recent_versions_with_children(self):
        self.section1.save_version(self.user, activity="test save")
        # grab the most recent version
        v = list(self.section1.version_set.all())[-1]
        # should not be any newer ones
        self.assertEqual(
            len(v.more_recent_versions()),
            0)
        # add another on a child
        self.section1.get_children()[0].save_version(
            self.user,
            activity="another test save")
        # now there should be
        self.assertEqual(
            len(v.more_recent_versions()),
            1)


class MultipleLevelsTest(TestCase):
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
        self.section3.add_child_section_from_dict(
            {
                'label': 'Section 4',
                'slug': 'section-4',
                'pageblocks': [],
                'children': [],
            })
        self.section4 = self.section3.get_children()[0]
        self.section4.add_child_section_from_dict(
            {
                'label': 'Section 5',
                'slug': 'section-5',
                'pageblocks': [],
                'children': [],
            })
        self.section5 = self.section4.get_children()[0]

    def tearDown(self):
        Hierarchy.objects.all().delete()

    def test_get_absolute_url(self):
        self.assertEqual(self.section4.get_absolute_url(),
                         "section-3/section-4/")

    def test_get_edit_url(self):
        self.assertEqual(self.section4.get_edit_url(),
                         "edit/section-3/section-4/")

    def test_get_absolute_url_two_down(self):
        self.assertEqual(self.section5.get_absolute_url(),
                         "section-3/section-4/section-5/")

    def test_get_edit_url_two_down(self):
        self.assertEqual(self.section5.get_edit_url(),
                         "edit/section-3/section-4/section-5/")

    def test_clone_hierarchy(self):
        self.section1.add_pageblock_from_dict({
            'block_type': 'Test Block',
            'body': 'test body',
        })
        duplicate = Hierarchy.clone(self.h, 'foo', '/foo/')

        descendants = duplicate.get_root().get_descendants()
        self.assertTrue(descendants[0].label, 'Section 1')
        self.assertTrue(descendants[0].depth, 1)
        self.assertEqual(descendants[0].pageblock_set.count(), 1)

        self.assertTrue(descendants[1].label, 'Section 2')
        self.assertTrue(descendants[1].depth, 1)

        self.assertTrue(descendants[2].label, 'Section 3')
        self.assertTrue(descendants[2].depth, 1)

        self.assertTrue(descendants[3].label, 'Section 4')
        self.assertTrue(descendants[3].depth, 2)

        self.assertTrue(descendants[4].label, 'Section 5')
        self.assertTrue(descendants[4].depth, 3)


class SectionTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.section = RootSectionFactory()

    def test_add_pageblock_from_dict(self):
        self.section.add_pageblock_from_dict({
            'block_type': 'Test Block',
            'body': 'test body',
        })
        block = self.section.pageblock_set.first()
        assert (block is not None)
        self.assertEqual(block.block().body, 'test body')
        self.assertEqual(
            self.section.pageblock_set.first(), block,
            'The PageBlock has been added to the Section')

    def test_empty_section_is_unlocked(self):
        self.assertTrue(self.section.unlocked(self.user))

    def test_section_with_test_block_is_unlocked(self):
        self.section.add_pageblock_from_dict({'block_type': 'Test Block'})
        self.assertEqual(self.section.pageblock_set.count(), 1)

        # TestBlock doesn't have an "unlocked" method defined, so this
        # tests that Section.unlocked() handles that case.
        self.assertTrue(self.section.unlocked(self.user))


class TestBlockTest(TestCase):
    def setUp(self):
        self.b = TestBlockFactory()

    def test_is_valid_from_factory(self):
        self.b.full_clean()

    def test_create_from_dict(self):
        testblock = TestBlock.create_from_dict({
            'body': 'abc',
        })
        self.assertEqual(testblock.display_name, 'Test Block')
        self.assertEqual(testblock.body, 'abc')


class UserPageVisitTest(TestCase):
    def test_is_valid_from_factory(self):
        upv = UserPageVisitFactory()
        upv.full_clean()
