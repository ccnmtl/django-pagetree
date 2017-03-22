from __future__ import unicode_literals

from django import forms
from django.utils.text import slugify
from treebeard.forms import movenodeform_factory
from pagetree.models import Hierarchy, Section


class CloneHierarchyForm(forms.ModelForm):
    class Meta:
        model = Hierarchy
        fields = ['name', 'base_url']

    class Media:
        css = {
            'all': ('pagetree/css/loading.css',)
        }
        js = ('pagetree/js/src/clone-loading.js',)

    base_url = forms.CharField(
        required=False, label='Base URL (optional)')

    def clean(self):
        cleaned_data = super(CloneHierarchyForm, self).clean()
        name = cleaned_data.get('name')
        base_url = cleaned_data.get('base_url')
        if not base_url:
            # If there's no base_url, derive it from the name.
            cleaned_data['base_url'] = slugify(name)
            base_url = cleaned_data['base_url']

        if Hierarchy.objects.filter(name=name).exists():
            raise forms.ValidationError(
                'There\'s already a hierarchy with the name: {}'.format(
                    name))

        if Hierarchy.objects.filter(base_url=base_url).exists():
            raise forms.ValidationError(
                'There\'s already a hierarchy with the base_url: {}'.format(
                    base_url))

        return cleaned_data


MoveSectionForm = movenodeform_factory(
    Section,
    exclude=('label', 'slug', 'hierarchy', 'show_toc', 'deep_toc')
)
