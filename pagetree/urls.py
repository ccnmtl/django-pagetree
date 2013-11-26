from django.conf.urls import patterns
import os.path
media_root = os.path.join(os.path.dirname(__file__), "media")

urlpatterns = patterns(
    '',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': media_root}),
)

urlpatterns += patterns(
    'pagetree.views',
    (r'^reorder_pageblocks/(?P<section_id>\d+)/$', 'reorder_pageblocks', {},
     "reorder-pageblocks"),
    (r'^reorder_section_children/(?P<section_id>\d+)/$',
     'reorder_section_children', {}, "reorder-section-children"),
    (r'^section/add/(?P<section_id>\d+)/$', 'add_child_section', {},
     "add-child-section"),
    (r'^section/move/(?P<section_id>\d+)/$', 'move_section', {},
     "move-section"),
    (r'^pageblock/add/(?P<section_id>\d+)/$', 'add_pageblock', {},
     "add-pageblock"),
    (r'^pageblock/edit/(?P<pageblock_id>\d+)/$', 'edit_pageblock', {},
     "edit-pageblock"),
    (r'^pageblock/jsonexport/(?P<pageblock_id>\d+)/$', 'export_pageblock_json',
     {}, "export-pageblock-json"),
    (r'^pageblock/jsonimport/(?P<pageblock_id>\d+)/$', 'import_pageblock_json',
     {}, "import-pageblock-json"),
    (r'^delete_section/(?P<section_id>\d+)/$', 'delete_section', {},
     "delete-section"),
    (r'^edit_section/(?P<section_id>\d+)/$', 'edit_section', {},
     "edit-section"),
    (r'^delete_pageblock/(?P<pageblock_id>\d+)/$', 'delete_pageblock', {},
     "delete-pageblock"),
    (r'^create_tree_root$', 'create_tree_root', {}, "create_tree_root"),
    (r'^export/$', 'exporter', {}, 'export-hierarchy'),
    (r'^version/(?P<version_id>\d+)/revert/$', 'revert_to_version', {},
     "revert-to-version"),
)
