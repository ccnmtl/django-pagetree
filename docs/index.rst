.. Pagetree documentation master file, created by
   sphinx-quickstart on Wed Mar 11 14:59:53 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pagetree's documentation!
====================================

Pagetree is a helper for building sites that are organized
as a hierarchy of pages which the user/visitor goes through
in (depth-first) order.

The pages can then each have 'blocks' attached to them which
are content or interactive things.

See `django-pageblocks <https://github.com/ccnmtl/django-pageblocks>`_
for a basic set of these blocks.

Pagetree is designed to allow this kind of site to be built by
an editor through the web. It aims to provide the minimum amount
of functionality possible and stay out of the way as much
as possible.

.. toctree::
   :maxdepth: 2

   installation
   custom_pageblocks
   API
   glossary
