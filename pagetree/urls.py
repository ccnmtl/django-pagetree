from django.conf.urls.defaults import patterns

urlpatterns = patterns('pagetree.views',
                       (r'^reorder_pageblocks/$', 'reorder_pageblocks'),
                       (r'^reorder_section_children/(?P<id>\d+)/','reorder_section_children'),
                       (r'^delete_pageblock/(?P<id>\d+)/$','delete_pageblock'),
                       (r'^edit_pageblock/(?P<id>\d+)/$','edit_pageblock'),
                       (r'^delete_section/(?P<id>\d+)/$','delete_section'),
                       (r'^edit_section/(?P<id>\d+)/$','edit_section'),
                       (r'^section/(?P<id>\d+)/add_pageblock/$','add_pageblock'),
)
