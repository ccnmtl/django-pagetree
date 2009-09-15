from django.conf.urls.defaults import patterns

urlpatterns = patterns('pagetree.views',
                       (r'^reorder_pageblocks/$', 'reorder_pageblocks'),
                       (r'^reorder_section_children/(?P<id>\d+)/','reorder_section_children'),
)
