from __future__ import unicode_literals

"""
Generic View functions.

The idea here is to provide basic functionality. These view functions
should not be routed to directly. Instead, your application should
have its own views which import these functions, enforce their own
authentication/authorization rules, and then call these functions,
overriding behavior where needed.

Ie, you would do something like:

from pagetree.generic.views import PageView, EditView


class MyPageView(PageView):
    def get_extra_context(self):
        ctx = super(MyPageView, self).get_extra_context()
        # Add extra context data
        return ctx

    def dispatch(self, request, *args, **kwargs):
        # Example of a redirect based on user state
        if not request.user.profile.avatar:
            return redirect(reverse('avatar-selector'))

        return super(MyPageView, self).dispatch(request, *args, **kwargs)


class MyEditView(EditView):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Do any additional auth here
        return super(MyEditView, self).dispatch(
            request, *args, **kwargs)

"""
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView

from pagetree.forms import CloneHierarchyForm
from pagetree.helpers import get_section_from_path
from pagetree.models import Hierarchy


def has_responses(section):
    for p in section.pageblock_set.all():
        block = p.block()
        if hasattr(block, 'needs_submit') and block.needs_submit():
            return True

    return False


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


class UserPageVisitor(object):
    """ simplify/centralize logging visits

    automatically does nothing for an anonymous user
    """
    def __init__(self, section, user):
        self.section = section
        self.user = user

    def visit(self, status=None):
        if self.user.is_anonymous:
            return
        if not status:
            prev = self.section.get_uservisit(self.user)
            if prev is None:
                status = "complete"
                if self.section.needs_submit():
                    status = "incomplete"
            else:
                status = prev.status
        self.section.user_pagevisit(self.user, status)


def generic_view_page(request, path, hierarchy="main",
                      gated=False,
                      template="pagetree/page.html",
                      extra_context=None,
                      no_root_fallback_url="/admin/"
                      ):
    """ generic pagetree page view

    needs the request and path
    hierarchy -> defaults to "main"
    gated -> whether to block users from skipping ahead (ie,
             force sequential access)
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
    module = section.get_module()
    if section.is_root():
        return visit_root(section, no_root_fallback_url)

    if gated:
        # we need to check that they have visited all previous pages
        # first
        allow, first = section.gate_check(request.user)
        if not allow:
            # redirect to the first one that they need to visit
            return HttpResponseRedirect(first.get_absolute_url())
    upv = UserPageVisitor(section, request.user)
    if request.method == "POST":
        # user has submitted a form. deal with it
        if request.POST.get('action', '') == 'reset':
            upv.visit(status="incomplete")
            return reset_page(section, request)
        upv.visit(status="complete")
        return page_submit(section, request)
    else:
        allow_redo = False
        needs_submit = section.needs_submit()
        if needs_submit:
            allow_redo = section.allow_redo()
        upv.visit()
        instructor_link = has_responses(section)
        context = dict(
            section=section,
            module=module,
            needs_submit=needs_submit,
            allow_redo=allow_redo,
            is_submitted=section.submitted(request.user),
            modules=root.get_children(),
            root=section.hierarchy.get_root(),
            instructor_link=instructor_link,
        )
        if extra_context:
            context.update(extra_context)
        return render(request, template, context)


class SectionMixin(object):
    def get_section(self, path):
        return get_section_from_path(
            path,
            hierarchy_name=self.hierarchy_name,
            hierarchy_base=self.hierarchy_base)

    def get_extra_context(self):
        return self.extra_context

    def perform_checks(self, request, path):
        return None


class PageView(SectionMixin, View):
    template_name = "pagetree/page.html"
    hierarchy_name = "main"
    hierarchy_base = "/"
    extra_context = dict()
    gated = False
    no_root_fallback_url = "/admin/"

    def get_gated(self):
        return self.gated

    def gate_check(self, user):
        if not self.get_gated():
            return None

        # If this view is gated, and we have no user or an anonymous
        # user, then just deny access.
        if (not user) or user.is_anonymous:
            raise PermissionDenied()

        # we need to check that they have visited all previous pages
        # first
        allow, first = self.section.gate_check(user)
        if not allow:
            # redirect to the first one that they need to visit
            return HttpResponseRedirect(first.get_absolute_url())

    def perform_checks(self, request, path):
        self.section = self.get_section(path)
        self.root = self.section.hierarchy.get_root()
        self.module = self.section.get_module()
        if self.section.is_root():
            return visit_root(self.section, self.no_root_fallback_url)
        r = self.gate_check(request.user)
        if r is not None:
            return r
        self.upv = UserPageVisitor(self.section, request.user)
        return None

    def dispatch(self, request, *args, **kwargs):
        path = kwargs['path']
        rv = self.perform_checks(request, path)
        if rv is not None:
            return rv
        return super(PageView, self).dispatch(request, *args, **kwargs)

    def post(self, request, path):
        # user has submitted a form. deal with it
        if request.POST.get('action', '') == 'reset':
            self.upv.visit(status="incomplete")
            return reset_page(self.section, request)
        self.upv.visit(status="complete")
        return page_submit(self.section, request)

    def get(self, request, path):
        allow_redo = False
        needs_submit = self.section.needs_submit()
        if needs_submit:
            allow_redo = self.section.allow_redo()
        self.upv.visit()
        instructor_link = has_responses(self.section)
        context = dict(
            section=self.section,
            module=self.module,
            needs_submit=needs_submit,
            allow_redo=allow_redo,
            is_submitted=self.section.submitted(request.user),
            modules=self.root.get_children(),
            root=self.section.hierarchy.get_root(),
            instructor_link=instructor_link,
        )
        context.update(self.get_extra_context())
        return render(request, self.template_name, context)


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

    quizzes = []
    for p in section.pageblock_set.all():
        block = p.block()
        if hasattr(block, 'needs_submit') and block.needs_submit():
            return quizzes.append(block)

    context = dict(section=section,
                   quizzes=quizzes,
                   module=section.get_module(),
                   modules=root.get_children(),
                   root=section.hierarchy.get_root())
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)


class InstructorView(SectionMixin, TemplateView):
    template_name = "pagetree/instructor_page.html"
    hierarchy_name = "main"
    hierarchy_base = "/"
    extra_context = dict()

    def dispatch(self, request, *args, **kwargs):
        path = kwargs['path']
        rv = self.perform_checks(request, path)
        if rv is not None:
            return rv
        return super(InstructorView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        path = kwargs['path']
        section = self.get_section(path)
        root = section.hierarchy.get_root()

        quizzes = []
        for p in section.pageblock_set.all():
            block = p.block()
            if hasattr(block, 'needs_submit') and block.needs_submit():
                return quizzes.append(block)

        context = dict(section=section,
                       quizzes=quizzes,
                       module=section.get_module(),
                       modules=root.get_children(),
                       root=section.hierarchy.get_root())
        context.update(self.get_extra_context())
        return context


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
        module=section.get_module(),
        modules=root.get_children(),
        available_pageblocks=section.available_pageblocks(),
        root=section.hierarchy.get_root())
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)


class EditView(SectionMixin, TemplateView):
    template_name = "pagetree/edit_page.html"
    hierarchy_name = "main"
    hierarchy_base = "/"
    extra_context = dict()

    def dispatch(self, request, *args, **kwargs):
        path = kwargs['path']
        rv = self.perform_checks(request, path)
        if rv is not None:
            return rv
        return super(EditView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, path):
        section = self.get_section(path)
        root = section.hierarchy.get_root()
        context = dict(
            section=section,
            module=section.get_module(),
            modules=root.get_children(),
            available_pageblocks=section.available_pageblocks(),
            root=section.hierarchy.get_root())
        context.update(self.get_extra_context())
        return context


class CloneHierarchyView(FormView):
    template_name = "pagetree/clone_hierarchy.html"
    form_class = CloneHierarchyForm

    def get_context_data(self, **kwargs):
        context = super(CloneHierarchyView, self).get_context_data(**kwargs)

        hierarchy_id = self.kwargs.get('hierarchy_id')
        context['hierarchy'] = get_object_or_404(Hierarchy, id=hierarchy_id)

        return context

    def form_valid(self, form):
        hierarchy_id = self.kwargs.get('hierarchy_id')
        original = get_object_or_404(Hierarchy, id=hierarchy_id)

        name = form.cleaned_data['name']
        base_url = form.cleaned_data['base_url']

        clone = Hierarchy.clone(original, name, base_url)

        self.success_url = clone.get_root().get_edit_url()
        return super(CloneHierarchyView, self).form_valid(form)
