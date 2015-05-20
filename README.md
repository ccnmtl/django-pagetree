[![Latest Version](https://pypip.in/version/django-pagetree/badge.svg)](https://pypi.python.org/pypi/django-pagetree/)
[![Build Status](https://travis-ci.org/ccnmtl/django-pagetree.svg?branch=master)](https://travis-ci.org/ccnmtl/django-pagetree)

pagetree is a helper for building sites that are organized
as a hierarchy of pages which the user/visitor goes through
in (depth-first) order.

the pages can then each have 'blocks' attached to them which
are content or interactive things.

see django-pageblocks for a basic set of these blocks.

pagetree is designed to allow this kind of site to be built by
an editor through the web. it aims to provide the minimum amount
of functionality possible and stay out of the way as much
as possible.

# Documentation

Documentation for pagetree is on
[readthedocs](https://django-pagetree.readthedocs.org).

## Note on South and Django 1.7

1.0.0+ supports both South migrations and Django 1.7's built-in
migrations. If you are using Django 1.7+, everything should just
work. Dont' worry about it. If you are still on Django <1.7 and using
South, you *will* need to upgrade to South 1.0+.

Support for Django <1.7 and South will be dropped with version 2.0.0.
