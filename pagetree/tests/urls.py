from django.conf.urls import patterns, include
from pagetree.generic.views import EditView, InstructorView, PageView

urlpatterns = patterns(
    '',
    (r'^pagetree/', include('pagetree.urls')),
    # instantiate generic views using a template that doesn't
    # extend/depend on base.html
    (r'^pages/edit/(?P<path>.*)$',
     EditView.as_view(template_name="pagetree/test_page.html"),
     {}, 'edit-page'),
    (r'^pages/instructor/(?P<path>.*)$',
     InstructorView.as_view(template_name="pagetree/test_page.html")),
    (r'^pages/(?P<path>.*)$',
     PageView.as_view(template_name="pagetree/test_page.html")),
)
