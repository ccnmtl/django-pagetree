from __future__ import unicode_literals

from django import forms
from treebeard.forms import movenodeform_factory
from pagetree.models import Hierarchy, Section


class CloneHierarchyForm(forms.ModelForm):
    class Meta:
        model = Hierarchy
        fields = ['name', 'base_url']

    def clean(self):
        cleaned_data = super(CloneHierarchyForm, self).clean()
        name = cleaned_data.get('name')
        base_url = cleaned_data.get('base_url')

        if Hierarchy.objects.filter(name=name).count() > 0:
            raise forms.ValidationError(
                'There\'s already a hierarchy with the name: {}'.format(
                    name))

        if Hierarchy.objects.filter(base_url=base_url).count() > 0:
            raise forms.ValidationError(
                'There\'s already a hierarchy with the base_url: {}'.format(
                    base_url))

        return cleaned_data


MoveSectionForm = movenodeform_factory(
    Section,
    exclude=('label', 'slug', 'hierarchy', 'show_toc', 'deep_toc')
)
