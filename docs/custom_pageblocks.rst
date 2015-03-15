Custom Pageblocks
=================

.. currentmodule:: pagetree.generic.models

Sometimes you might want to define a custom pageblock type specific to
your application.

It's possible to define a custom pageblock from scratch by defining a
model with all the necessary hooks and a ``GenericRelation`` to Pagetree's
``PageBlock`` class. For convenience, Pagetree provides ``BasePageBlock``
that contains the basics you'll need for making a custom pageblock.

Here's an example of a custom pageblock::

  from django import forms
  from pagetree.generic.models import BasePageBlock


  class MyBlock(BasePageBlock):
      display_name = 'My Block Name'
      template_file = 'main/my_block.html'
      css_template_file = 'main/my_block.css'
      js_template_file = 'main/my_block.js'

      @staticmethod
      def add_form():
          return MyBlockForm()

      def edit_form(self):
          return MyBlockForm(instance=self)

      @staticmethod
      def create(request):
          form = MyBlockForm(request.POST)
          return form.save()

      @classmethod
      def create_from_dict(cls, d):
          return cls.objects.create(**d)

      def edit(self, vals, files):
          form = MyBlockForm(data=vals, files=files, instance=self)
          if form.is_valid():
              form.save()


  class MyBlockForm(forms.ModelForm):
      class Meta:
          model = MyBlock

Here's a list of methods and properties you can override in your
``BasePageBlock`` subclass:

.. autoclass:: BasePageBlock
   :members:
