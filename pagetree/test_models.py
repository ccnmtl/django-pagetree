from __future__ import unicode_literals

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import smart_str

from pagetree.generic.models import BasePageBlock
from pagetree.reports import ReportableInterface, ReportColumnInterface


class TestReportColumn(ReportColumnInterface):

    def identifier(self):
        return "Test Report Column"

    def metadata(self):
        return ['', self.identifier(), "generic",
                "string", "this is a test"]

    def user_value(self, user):
        return user.username


class TestBlock(BasePageBlock):
    """ this is a pageblock that is exclusively for pagetree's
    internal tests so we have some kind of block to test with
    without having to pull in the whole django-pageblocks
    package and its dependencies.

    You should never use it. In fact, forget that you ever saw this.
    """

    class Meta:
        app_label = 'pagetree'

    def __init__(self, *args, **kwargs):
        ContentType.objects.get_or_create(
            app_label='pagetree', model='testblock')
        super().__init__(*args, **kwargs)

    body = models.TextField(blank=True)

    template_file = "pagetree/testblock.html"
    display_name = "Test Block"

    def __str__(self):
        return smart_str(self.pageblock())

    def pageblock(self):
        return self.pageblocks.first()

    @classmethod
    def add_form(cls):
        class AddForm(forms.Form):
            body = forms.CharField(
                widget=forms.widgets.Textarea(attrs={'cols': 80}))
        return AddForm()

    @classmethod
    def create(cls, request):
        return TestBlock.objects.create(body=request.POST.get('body', ''))

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(**d)

    def edit_form(self):
        class EditForm(forms.Form):
            body = forms.CharField(widget=forms.widgets.Textarea(),
                                   initial=self.body)
        return EditForm()

    def edit(self, vals, files):
        self.body = vals.get('body', '')
        self.save()

    def as_dict(self):
        d = super(TestBlock, self).as_dict()
        d['body'] = self.body
        return d

    def import_from_dict(self, d):
        self.body = d.get('body', '')
        self.save()

    def summary_render(self):
        if len(self.body) < 61:
            return self.body
        else:
            return self.body[:61] + "..."

    def report_metadata(self):
        return [TestReportColumn()]

    def report_values(self):
        return [TestReportColumn()]


ReportableInterface.register(TestBlock)
