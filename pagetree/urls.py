from django.conf.urls.defaults import patterns
import os.path
media_root = os.path.join(os.path.dirname(__file__),"media")


urlpatterns = patterns('pagetree.views',
                       (r'^reorder_pageblocks/(?P<id>\d+)/$', 'reorder_pageblocks',{},"reorder-pageblocks"),
                       (r'^reorder_section_children/(?P<id>\d+)/$','reorder_section_children',{},"reorder-section-children"),
                       (r'^section/add/(?P<section_id>\d+)/$', 'add_child_section', {}, "add-child-section"),
                       (r'^pageblock/add/(?P<section_id>\d+)/$', 'add_pageblock', {}, "add-pageblock"),
                       (r'^pageblock/edit/(?P<block_id>\d+)/$','edit_pageblock',{},"edit-pageblock"),
                       (r'^delete_section/(?P<id>\d+)/$','delete_section',{},"delete-section"),
                       (r'^edit_section/(?P<id>\d+)/$','edit_section',{},"edit-section"),
)
