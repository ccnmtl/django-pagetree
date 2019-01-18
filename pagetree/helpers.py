from __future__ import unicode_literals

from pagetree.models import Hierarchy
import warnings


def get_hierarchy(name="main", base_url="/"):
    if isinstance(name, Hierarchy):
        # sometimes it makes things simpler in other areas
        # when the 'h' object being passed around may be
        # a string or may already be a Hierarchy.
        # so let's be cool about that
        return name
    return Hierarchy.objects.get_or_create(
        name=name,
        defaults=dict(base_url=base_url))[0]


def get_section_from_path(path, hierarchy="main",
                          hierarchy_name=None, hierarchy_base="/"):
    # 'hierarchy_name' and 'hierarchy_base' pair are preferred
    # interface, but 'hierarchy' is the more common old version
    # so we have to support that as well. If name/base are set
    # we treat that as a signal that the caller is using the
    # new interface, so we ignore 'hierarchy'
    if hierarchy_name is None:
        hierarchy_name = hierarchy
    h = get_hierarchy(name=hierarchy_name, base_url=hierarchy_base)
    return h.get_section_from_path(path)


def get_module(section):
    warnings.warn(
        (
            "pagetree.helpers.get_module is deprecated "
            "in favor of Section.get_module()"))
    return section.get_module()


def needs_submit(section):
    warnings.warn(
        (
            "pagetree.helpers.needs_submit is deprecated "
            "in favor of Section.needs_submit()"))
    return section.needs_submit()


def submitted(section, user):
    warnings.warn(
        (
            "pagetree.helpers.submitted is deprecated "
            "in favor of Section.submitted()"))
    return section.submitted(user)


def block_submitted(block, user):
    if user.is_anonymous:
        # anon can't have submitted a block
        return False
    if hasattr(block, 'needs_submit'):
        if block.needs_submit():
            try:
                s = block.unlocked(user)
                if not s:
                    return False
            except AttributeError:
                pass
    return True
