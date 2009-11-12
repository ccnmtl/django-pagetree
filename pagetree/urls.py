from django.conf.urls.defaults import patterns

urlpatterns = patterns('pagetree.views',
                       (r'^reorder_pageblocks/(?P<id>\d+)/', 'reorder_pageblocks',{},"reorder-pageblocks"),
                       (r'^reorder_section_children/(?P<id>\d+)/','reorder_section_children',{},"reorder-section-children"),
                       (r'^delete_pageblock/(?P<id>\d+)/$','delete_pageblock',{},"delete-pageblock"),
                       (r'^edit_pageblock/(?P<id>\d+)/$','edit_pageblock',{},"edit-pageblock"),
                       (r'^delete_section/(?P<id>\d+)/$','delete_section',{},"delete-section"),
                       (r'^edit_section/(?P<id>\d+)/$','edit_section',{},"edit-section"),
                       (r'^section/(?P<id>\d+)/add_pageblock/$','add_pageblock',{},"add-pageblock"),
                       (r'^section/(?P<id>\d+)/add_child_section/$','add_child_section',{},"add-child-section"),
)
