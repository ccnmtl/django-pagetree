from treebeard.forms import movenodeform_factory
from pagetree.models import Section


MoveSectionForm = movenodeform_factory(
    Section,
    exclude=('label', 'slug', 'hierarchy', 'show_toc', 'deep_toc')
)
