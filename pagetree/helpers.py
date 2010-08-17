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

def submitted(section,user):
    """ if all blocks on the page that require submissions
    have been submitted """
    for p in section.pageblock_set.all():
        if hasattr(p.block(),'needs_submit'):
            if p.block().needs_submit():
                try:
                    s = p.block().unlocked(user)
                    if not s:
                        # there's an unsubmitted block
                        return False
                except:
                    # most likely: no unlocked() method
                    pass
    # made it all the way through without any blocks
    # reporting that they are unsubmitted
    return True

def block_submitted(block,user):
    if user.is_anonymous():
        # anon can't have submitted a block
        return False
    if hasattr(block,'needs_submit'):
        if block.needs_submit():
            try:
                s = block.unlocked(user)
                if not s:
                    return False
            except:
                pass
    return True
