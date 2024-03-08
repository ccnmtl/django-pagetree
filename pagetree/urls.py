from __future__ import unicode_literals

import os.path

from django.urls import re_path
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
    re_path(r'^media/(?P<path>.*)$', django.views.static.serve,
            {'document_root': media_root}),
]

urlpatterns += [
    re_path(r'^reorder_pageblocks/(?P<section_id>\d+)/$', reorder_pageblocks,
            {}, "reorder-pageblocks"),
    re_path(r'^reorder_section_children/(?P<section_id>\d+)/$',
            reorder_section_children, {}, "reorder-section-children"),
    re_path(r'^section/add/(?P<section_id>\d+)/$', add_child_section, {},
            "add-child-section"),
    re_path(r'^section/move/(?P<section_id>\d+)/$', move_section, {},
            "move-section"),
    re_path(r'^pageblock/add/(?P<section_id>\d+)/$', add_pageblock, {},
            "add-pageblock"),
    re_path(r'^pageblock/edit/(?P<pageblock_id>\d+)/$', edit_pageblock, {},
            "edit-pageblock"),
    re_path(r'^pageblock/jsonexport/(?P<pageblock_id>\d+)/$',
            export_pageblock_json, {}, "export-pageblock-json"),
    re_path(r'^pageblock/jsonimport/(?P<pageblock_id>\d+)/$',
            import_pageblock_json, {}, "import-pageblock-json"),
    re_path(r'^delete_section/(?P<section_id>\d+)/$', delete_section, {},
            "delete-section"),
    re_path(r'^edit_section/(?P<section_id>\d+)/$', edit_section, {},
            "edit-section"),
    re_path(r'^delete_pageblock/(?P<pageblock_id>\d+)/$', delete_pageblock, {},
            "delete-pageblock"),
    re_path(r'^create_tree_root$', create_tree_root, {}, "create_tree_root"),
    re_path(r'^export/$', exporter, {}, 'export-hierarchy'),
    re_path(r'^version/(?P<version_id>\d+)/revert/$', revert_to_version, {},
            "revert-to-version"),
    re_path(r'^clone_hierarchy/(?P<hierarchy_id>\d+)/$',
            CloneHierarchyView.as_view(), name="clone-hierarchy"),
]
