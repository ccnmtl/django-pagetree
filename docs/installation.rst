Installation
============

You can install ``django-pagetree`` through ``pip``::

  $ pip install django-pagetree

In your project, add ``django-pagetree`` to your ``requirements.txt``.

Add to ``INSTALLED_APPS`` in your ``settings.py``::

  'pagetree',

The ``PAGEBLOCKS`` variable in your ``settings.py`` determines which
pageblocks will be available on your site::

  PAGEBLOCKS = [
      'pageblocks.TextBlock',
      'pageblocks.HTMLBlock',
  ]

To use these pageblocks, you'll need to put ``django-pageblocks`` in your
``requirements.txt``, and add ``'pageblocks'`` to your ``INSTALLED_APPS``.

Pagetree provides a set of generic views that you can use to build a
barebones site out of the box. In your ``urls.py``, you will need to import
the generic views::

  from pagetree.generic.views import PageView, EditView, InstructorView

Then add the following URL routes::

  (r'^pagetree/', include('pagetree.urls')),
  (r'^pages/edit/(?P<path>.*)$',
   EditView.as_view(hierarchy_name="main", hierarchy_base="/pages/"),
   {}, 'edit-page'),
  (r'^pages/instructor/(?P<path>.*)$',
   InstructorView.as_view(
       hierarchy_name="main", hierarchy_base="/pages/")),
  (r'^pages/(?P<path>.*)$',
   PageView.as_view(hierarchy_name="main", hierarchy_base="/pages/")),
