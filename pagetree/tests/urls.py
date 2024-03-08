from __future__ import unicode_literals

from django.urls import include, re_path
from pagetree.generic.views import EditView, InstructorView, PageView

urlpatterns = [
    re_path(r'^pagetree/', include('pagetree.urls')),

    # instantiate generic views using a template that doesn't
    # extend/depend on base.html
    re_path(r'^pages/edit/(?P<path>.*)$',
            EditView.as_view(template_name="pagetree/test_page.html"),
            {}, 'edit-page'),
    re_path(r'^pages/instructor/(?P<path>.*)$',
            InstructorView.as_view(template_name="pagetree/test_page.html")),
    re_path(r'^pages/(?P<path>.*)$',
            PageView.as_view(template_name="pagetree/test_page.html")),

    # a second set to make sure non-default hierarchies
    # get handled as well
    re_path(r'^pages2/edit/(?P<path>.*)$',
            EditView.as_view(
                hierarchy_name="two",
                hierarchy_base="/pages2",
                template_name="pagetree/test_page.html"),
            {}, 'edit-page'),
    re_path(r'^pages2/instructor/(?P<path>.*)$',
            InstructorView.as_view(
                hierarchy_name="two",
                hierarchy_base="/pages2",
                template_name="pagetree/test_page.html")),
    re_path(r'^pages2/(?P<path>.*)$',
            PageView.as_view(
                hierarchy_name="two",
                hierarchy_base="/pages2",
                template_name="pagetree/test_page.html")),
]
