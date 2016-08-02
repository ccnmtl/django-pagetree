from __future__ import unicode_literals

import os.path

from django.conf.urls import url
import django.views.static

from pagetree.generic.views import CloneHierarchyView
from .views import (
    reorder_pageblocks, reorder_section_children, add_child_section,
    move_section, revert_to_version, exporter, create_tree_root,
    delete_pageblock, edit_section, delete_section, add_pageblock,
    edit_pageblock, export_pageblock_json, import_pageblock_json,
)


media_root = os.path.join(os.path.dirname(__file__), "media")

urlpatterns = [
    url(r'^media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': media_root}),
]

urlpatterns += [
    url(r'^reorder_pageblocks/(?P<section_id>\d+)/$', reorder_pageblocks, {},
        "reorder-pageblocks"),
    url(r'^reorder_section_children/(?P<section_id>\d+)/$',
        reorder_section_children, {}, "reorder-section-children"),
    url(r'^section/add/(?P<section_id>\d+)/$', add_child_section, {},
        "add-child-section"),
    url(r'^section/move/(?P<section_id>\d+)/$', move_section, {},
        "move-section"),
    url(r'^pageblock/add/(?P<section_id>\d+)/$', add_pageblock, {},
        "add-pageblock"),
    url(r'^pageblock/edit/(?P<pageblock_id>\d+)/$', edit_pageblock, {},
        "edit-pageblock"),
    url(r'^pageblock/jsonexport/(?P<pageblock_id>\d+)/$',
        export_pageblock_json, {}, "export-pageblock-json"),
    url(r'^pageblock/jsonimport/(?P<pageblock_id>\d+)/$',
        import_pageblock_json, {}, "import-pageblock-json"),
    url(r'^delete_section/(?P<section_id>\d+)/$', delete_section, {},
        "delete-section"),
    url(r'^edit_section/(?P<section_id>\d+)/$', edit_section, {},
        "edit-section"),
    url(r'^delete_pageblock/(?P<pageblock_id>\d+)/$', delete_pageblock, {},
        "delete-pageblock"),
    url(r'^create_tree_root$', create_tree_root, {}, "create_tree_root"),
    url(r'^export/$', exporter, {}, 'export-hierarchy'),
    url(r'^version/(?P<version_id>\d+)/revert/$', revert_to_version, {},
        "revert-to-version"),
    url(r'^clone_hierarchy/(?P<hierarchy_id>\d+)/$',
        CloneHierarchyView.as_view(), name="clone-hierarchy"),
]
