from models import Hierarchy
import warnings


def get_hierarchy(name="main"):
    return Hierarchy.objects.get_or_create(
        name=name,
        defaults=dict(base_url="/"))[0]


def get_section_from_path(path, hierarchy="main"):
    h = get_hierarchy(hierarchy)
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
    if user.is_anonymous():
        # anon can't have submitted a block
        return False
    if hasattr(block, 'needs_submit'):
        if block.needs_submit():
            try:
                s = block.unlocked(user)
                if not s:
                    return False
            except:
                pass
    return True
