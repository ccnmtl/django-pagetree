from django import forms
from treebeard.forms import movenodeform_factory
from pagetree.models import Hierarchy, Section


class CloneHierarchyForm(forms.ModelForm):
    class Meta:
        model = Hierarchy
        fields = ['name', 'base_url']


MoveSectionForm = movenodeform_factory(
    Section,
    exclude=('label', 'slug', 'hierarchy', 'show_toc', 'deep_toc')
)
