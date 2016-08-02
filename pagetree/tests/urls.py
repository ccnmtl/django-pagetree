from __future__ import unicode_literals

from django.conf.urls import include, url
from pagetree.generic.views import EditView, InstructorView, PageView

urlpatterns = [
    url(r'^pagetree/', include('pagetree.urls')),

    # instantiate generic views using a template that doesn't
    # extend/depend on base.html
    url(r'^pages/edit/(?P<path>.*)$',
        EditView.as_view(template_name="pagetree/test_page.html"),
        {}, 'edit-page'),
    url(r'^pages/instructor/(?P<path>.*)$',
        InstructorView.as_view(template_name="pagetree/test_page.html")),
    url(r'^pages/(?P<path>.*)$',
        PageView.as_view(template_name="pagetree/test_page.html")),

    # a second set to make sure non-default hierarchies
    # get handled as well
    url(r'^pages2/edit/(?P<path>.*)$',
        EditView.as_view(
            hierarchy_name="two",
            hierarchy_base="/pages2",
            template_name="pagetree/test_page.html"),
        {}, 'edit-page'),
    url(r'^pages2/instructor/(?P<path>.*)$',
        InstructorView.as_view(
            hierarchy_name="two",
            hierarchy_base="/pages2",
            template_name="pagetree/test_page.html")),
    url(r'^pages2/(?P<path>.*)$',
        PageView.as_view(
            hierarchy_name="two",
            hierarchy_base="/pages2",
            template_name="pagetree/test_page.html")),
]
