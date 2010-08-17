from models import Hierarchy

def get_hierarchy(name="main"):
    return Hierarchy.objects.get_or_create(name=name,
                                           defaults=dict(base_url="/"))[0]

def get_section_from_path(path,hierarchy="main"):
    h = get_hierarchy(hierarchy)
    return h.get_section_from_path(path)

def get_module(section):
    """ get the top level module that the section is in"""
    if section.is_root:
        return None
    return section.get_ancestors()[1]

def needs_submit(section):
    """ if any blocks on the page need to be submitted """
    for p in section.pageblock_set.all():
        if hasattr(p.block(),'needs_submit'):
            if p.block().needs_submit():
                return True
    return False
