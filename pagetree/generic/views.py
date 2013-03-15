"""
Generic View functions.

The idea here is to provide basic functionality. These view functions
should not be routed to directly. Instead, your application should
have its own views which import these functions, enforce their own
authentication/authorization rules, and then call these functions,
overriding behavior where needed.

Ie, you would do something like:

from pagetree.generic.views import pageview, pageedit

def page(request, path):
    # do auth on the request if you need the user to be logged in
    # or only want some particular users to be able to get here
    return pageview(request, path, template="main/page.html",
        extra_context=dict(some_other="pass this through to the template"))

@login_required
def edit_page(request, path):
    # do any additional auth here
    return pageedit(request, path)

"""
from django.shortcuts import render
from django.http import HttpResponseRedirect
from pagetree.helpers import get_module, needs_submit, submitted
from pagetree.helpers import get_section_from_path


def has_responses(section):
    quizzes = [p.block() for p in section.pageblock_set.all()
               if hasattr(p.block(), 'needs_submit')
               and p.block().needs_submit()]
    return quizzes != []


def visit_root(section, fallback_url="/admin/"):
    """ if they try to visit the root, we need to send them
    either to the first section on the site, or to
    the admin page if there are no sections (so they
    can add some)"""
    if section.get_next():
        # just send them to the first child
        return HttpResponseRedirect(section.get_next().get_absolute_url())
    # no sections available so
    # send them to the fallback
    return HttpResponseRedirect(fallback_url)


def page_submit(section, request):
    proceed = section.submit(request.POST, request.user)
    if proceed:
        next_section = section.get_next()
        if next_section:
            return HttpResponseRedirect(next_section.get_absolute_url())
        else:
            # they are on the "last" section of the site
            # all we can really do is send them back to this page
            return HttpResponseRedirect(section.get_absolute_url())
    # giving them feedback before they proceed
    return HttpResponseRedirect(section.get_absolute_url())


def reset_page(section, request):
    section.reset(request.user)
    return HttpResponseRedirect(section.get_absolute_url())


def generic_view_page(request, path, hierarchy="main",
                      template="pagetree/page.html",
                      extra_context=None,
                      no_root_fallback_url="/admin/"
                      ):
    """ generic pagetree page view

    needs the request and path
    hierarchy -> defaults to "main"
    template -> defaults to "pagetree/page.html" so you can either
                override that, or pass in a different one here (or
                just use the basic one that pagetree includes)
    extra_context -> dict of additional variables to pass along to the
                     template
    no_root_fallback -> where to send the user if there are no sections
                        at all in the tree (not even a root). defaults to
                        "/admin/"
    """
    section = get_section_from_path(path, hierarchy=hierarchy)
    root = section.hierarchy.get_root()
    module = get_module(section)
    if section.is_root():
        return visit_root(section, no_root_fallback_url)

    if request.method == "POST":
        # user has submitted a form. deal with it
        if request.POST.get('action', '') == 'reset':
            return reset_page(section, request)
        return page_submit(section, request)
    else:
        instructor_link = has_responses(section)
        context = dict(
            section=section,
            module=module,
            needs_submit=needs_submit(section),
            is_submitted=submitted(section, request.user),
            modules=root.get_children(),
            root=section.hierarchy.get_root(),
            instructor_link=instructor_link,
        )
        if extra_context:
            context.update(extra_context)
        return render(request, template, context)


def generic_instructor_page(request, path, hierarchy="main",
                            template="pagetree/instructor_page.html",
                            extra_context=None,
                            ):
    """ generic pagetree instructor view

    needs the request and path
    hierarchy -> defaults to "main"
    template -> defaults to "pagetree/instructor_page.html" so you can either
                override that, or pass in a different one here (or
                just use the basic one that pagetree includes)
    extra_context -> dict of additional variables to pass along to the
                     template
    """
    section = get_section_from_path(path, hierarchy=hierarchy)
    root = section.hierarchy.get_root()

    quizzes = [p.block() for p in section.pageblock_set.all()
               if hasattr(p.block(), 'needs_submit')
               and p.block().needs_submit()]
    context = dict(section=section,
                   quizzes=quizzes,
                   module=get_module(section),
                   modules=root.get_children(),
                   root=section.hierarchy.get_root())
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)


def generic_edit_page(request, path, hierarchy="main",
                      template="pagetree/edit_page.html",
                      extra_context=None,
                      ):
    """ generic pagetree edit page view

    needs the request and path
    hierarchy -> defaults to "main"
    template -> defaults to "pagetree/edit_page.html" so you can either
                override that, or pass in a different one here (or
                just use the basic one that pagetree includes)
    extra_context -> dict of additional variables to pass along to the
                     template
    """
    section = get_section_from_path(path, hierarchy=hierarchy)
    root = section.hierarchy.get_root()
    context = dict(
        section=section,
        module=get_module(section),
        modules=root.get_children(),
        available_pageblocks=section.available_pageblocks(),
        root=section.hierarchy.get_root())
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)
