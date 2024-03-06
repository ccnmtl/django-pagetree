from __future__ import unicode_literals

from django import forms
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.encoding import smart_str

from pagetree.models import PageBlock


class BasePageBlock(models.Model):
    """An abstract pageblock to be used for custom pageblocks."""

    class Meta:
        abstract = True

    pageblocks = GenericRelation(PageBlock)

    display_name = None
    """The name for this block that's used in pagetree's menus."""

    def as_dict(self):
        """Returns the PageBlock as a dictionary.

        :rtype: dictionary
        """
        return dict(block_type=self.display_name)

    def allow_redo(self):
        """Determines whether this block allows users to resubmit answers.

        This method is only used if ``needs_submit`` is True. If
        ``allow_redo`` is also True, pagetree will render a button
        with the text "I want to change my answers." when the block
        has been submitted.

        :returns: a boolean
        """

        return False

    def needs_submit(self):
        """Determines whether this pageblock needs form controls rendered.

        If ``needs_submit`` is True, then pagetree will create a <form>
        on this pageblock's surrounding page, and a Submit button for
        that form. It may also render a "Clear results" button, under
        the right circumstances. The surrounding <form> allows pagetree
        to handle form submissions for multiple blocks on the same page.

        Also, when ``needs_submit`` is True, the POST data on the
        Section's ``submit()`` step gets processed, but when needs_submit
        is False, nothing is sent to the server.

        :returns: a boolean
        """

        return False

    def unlocked(self, user):
        """Determines whether the user can proceed past this block.

        The current user is passed in to this function, allowing you to,
        for example, find out if that user has submitted the info
        necessary to proceed past this block's page.

        :param user: the current user
        :returns: a boolean
        """

        return True

    def submit(self, user, request_data):
        """This is a hook for handling this pageblock's form submission.

        :returns: None
        """

        pass

    def redirect_to_self_on_submit(self):
        """Determines where the user is redirected to on page submission.

        If ``redirect_to_self_on_submit`` returns True, then the user will
        be redirected to the current page when the page's form is
        submitted. Otherwise, they'll be redirected to the next page in
        the hierarchy.

        :returns: a boolean
        """

        return True

    def clear_user_submissions(self, user):
        """A hook to clear any user submissions for this block.

        :returns: None
        """

        pass

    def pageblock(self):
        return self.pageblocks.first()

    def __str__(self):
        return smart_str(self.pageblock())

    # TODO: I'd like to have all the following methods be inherited
    # somehow. For now these need to be copy and pasted for each custom
    # pageblock.
    @staticmethod
    def add_form():
        return BasePageBlockForm()

    def edit_form(self):
        return BasePageBlockForm(instance=self)

    @staticmethod
    def create(request):
        form = BasePageBlockForm(request.POST)
        return form.save()

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(**d)

    def edit(self, vals, files):
        form = BasePageBlockForm(data=vals, files=files, instance=self)
        if form.is_valid():
            form.save()


class BasePageBlockForm(forms.ModelForm):
    """Example ModelForm for the BasePageBlock.

    This is just an example. It should always be replaced with your
    own ModelForm pointing to the custom pageblock.
    """

    class Meta:
        model = BasePageBlock
        fields = '__all__'
