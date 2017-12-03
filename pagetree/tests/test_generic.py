from __future__ import unicode_literals

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client
from django.http import Http404
from django.contrib.auth.models import User
from pagetree.models import Hierarchy
from pagetree.generic.views import has_responses, visit_root
from pagetree.generic.views import UserPageVisitor
from pagetree.generic.views import generic_view_page
from pagetree.generic.views import generic_instructor_page
from pagetree.generic.views import generic_edit_page


class Anon(object):
    is_anonymous = True


class NonAnon(object):
    is_anonymous = False


class MockSection(object):
    def __init__(self, needs_submit_value=False):
        self.needs_submit_called = 0
        self.user_pagevisit_called = 0
        self.needs_submit_value = needs_submit_value

    def needs_submit(self):
        self.needs_submit_called += 1
        return self.needs_submit_value

    def user_pagevisit(self, user, status):
        self.user_pagevisit_called += 1
        self.user = user
        self.status = status

    def get_uservisit(self, user):
        return None


class UserPageVisitorTest(TestCase):
    def test_visit_anonymous(self):
        s = MockSection()
        upv = UserPageVisitor(s, Anon())
        upv.visit()
        self.assertEqual(s.needs_submit_called, 0)

    def test_visit_not_status(self):
        s = MockSection(needs_submit_value=False)
        upv = UserPageVisitor(s, NonAnon())
        upv.visit(status=False)
        self.assertEqual(s.needs_submit_called, 1)
        self.assertEqual(s.user_pagevisit_called, 1)
        self.assertEqual(s.status, "complete")

    def test_visit_not_status_needs_submit(self):
        s = MockSection(needs_submit_value=True)
        upv = UserPageVisitor(s, NonAnon())
        upv.visit(status=False)
        self.assertEqual(s.needs_submit_called, 1)
        self.assertEqual(s.user_pagevisit_called, 1)
        self.assertEqual(s.status, "incomplete")

    def test_visit_status(self):
        s = MockSection()
        upv = UserPageVisitor(s, NonAnon())
        upv.visit(status=True)
        self.assertEqual(s.needs_submit_called, 0)
        self.assertEqual(s.user_pagevisit_called, 1)
        self.assertEqual(s.status, True)


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


class GenericPageViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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

    def test_nonexistant(self):
        request = self.factory.get("/foo/")
        with self.assertRaises(Http404):
            generic_view_page(request, "/foo/")

    def test_root(self):
        request = self.factory.get("/")
        response = generic_view_page(request, "/")
        self.assertEqual(response.status_code, 302)

    def test_section1(self):
        request = self.factory.get("/section-1/")
        request.user = self.u
        response = generic_view_page(
            request, "section-1/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_section1_gated(self):
        request = self.factory.get("/section-1/")
        request.user = self.u
        response = generic_view_page(
            request, "section-1/",
            gated=True,
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_section2(self):
        request = self.factory.get("/section-2/")
        request.user = self.u
        response = generic_view_page(
            request, "section-2/",
            extra_context=dict(foo='bar'),
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_section2_gated(self):
        request = self.factory.get("/section-2/")
        request.user = self.u
        response = generic_view_page(
            request, "section-2/",
            gated=True,
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 302)

    def test_section1_post(self):
        request = self.factory.post("/section-1/", dict())
        request.user = self.u
        response = generic_view_page(
            request, "section-1/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 302)

    def test_section1_reset(self):
        request = self.factory.post("/section-1/", dict(action="reset"))
        request.user = self.u
        response = generic_view_page(
            request, "section-1/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 302)

    def test_section3_post(self):
        request = self.factory.post("/section-3/", dict())
        request.user = self.u
        response = generic_view_page(
            request, "section-3/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 302)

    def test_instructor_section1(self):
        request = self.factory.get("/instructor/section-1/")
        request.user = self.u
        response = generic_instructor_page(
            request, "section-1/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_edit_section1(self):
        request = self.factory.get("/edit/section-1/")
        request.user = self.u
        response = generic_edit_page(
            request, "section-1/",
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_instructor_section1_extra(self):
        request = self.factory.get("/instructor/section-1/")
        request.user = self.u
        response = generic_instructor_page(
            request, "section-1/",
            extra_context=dict(foo="bar"),
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)

    def test_edit_section1_extra(self):
        request = self.factory.get("/edit/section-1/")
        request.user = self.u
        response = generic_edit_page(
            request, "section-1/",
            extra_context=dict(foo="bar"),
            template="pagetree/test_page.html")
        self.assertEqual(response.status_code, 200)


class GenericPageViewURLConfTest(TestCase):
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

    def test_edit_section1(self):
        response = self.c.get("/pages/edit/section-1/")
        self.assertEqual(response.status_code, 200)

    def test_instructor_section1(self):
        response = self.c.get("/pages/instructor/section-1/")
        self.assertEqual(response.status_code, 200)

    def test_section1(self):
        response = self.c.get("/pages/section-1/")
        self.assertEqual(response.status_code, 200)


class GenericPageViewURLConfTestSecond(TestCase):
    """ make sure non default hierarchies also work """
    def setUp(self):
        self.h = Hierarchy.objects.create(name="two", base_url="/pages2")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'sec-1',
                'pageblocks': [],
                'children': [],
            })
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 2',
                'slug': 'sec-2',
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
                'slug': 'sec-3',
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

    def test_edit_section1(self):
        response = self.c.get("/pages2/edit/sec-1/")
        self.assertEqual(response.status_code, 200)

    def test_instructor_section1(self):
        response = self.c.get("/pages2/instructor/sec-1/")
        self.assertEqual(response.status_code, 200)

    def test_section1(self):
        response = self.c.get("/pages2/sec-1/")
        self.assertEqual(response.status_code, 200)
