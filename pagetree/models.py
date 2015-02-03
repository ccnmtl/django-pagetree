from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django import forms
from django.template import Context
from django.template.loader import get_template
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import get_model
from django.template.defaultfilters import slugify
from json import dumps
from treebeard.mp_tree import MP_Node
import django.core.exceptions
from treebeard.forms import MoveNodeForm
from pagetree.reports import ReportableInterface, ReportColumnInterface


# dummy it out
class dummystatsd(object):
    def incr(self, metric):
        pass
statsd = dummystatsd()

try:
    from django_statsd.clients import statsd
except ImportError:
    pass

settings = None
from django.conf import settings


class Hierarchy(models.Model):
    name = models.CharField(max_length=256)
    base_url = models.CharField(max_length=256, default="")

    @staticmethod
    def get_hierarchy(name):
        return Hierarchy.objects.get_or_create(name=name,
                                               defaults=dict(base_url="/"))[0]

    def get_absolute_url(self):
        return self.base_url

    def __unicode__(self):
        return self.name

    def get_root(self):
        # will create it if it doesn't exist
        try:
            return Section.objects.get(hierarchy=self,
                                       label="Root").get_root()
        except Section.DoesNotExist:
            return Section.add_root(label="Root", slug="", hierarchy=self)

    def get_top_level(self):
        return self.get_root().get_children()

    def find_section_from_path(self, path):
        if path.endswith("/"):
            path = path[:-1]
        root = self.get_root()
        current = root
        if path == "":
            return current
        for slug in path.split("/"):
            slugs = dict()
            for c in current.get_children():
                slugs[c.slug] = c
            if slug in slugs:
                current = slugs[slug]
            else:
                return None
        return current

    def get_section_from_path(self, path):
        s = self.find_section_from_path(path)
        if s is None:
            raise Http404()
        return s

    def available_pageblocks(self):
        if hasattr(settings, 'PAGEBLOCKS') and settings.PAGEBLOCKS is not None:
            return [get_model(*pb.split('.')) for pb in settings.PAGEBLOCKS]
        else:
            return []

    def get_first_leaf(self, section):
        if section.is_leaf():
            return section
        return self.get_first_leaf(section.get_children()[0])

    def get_last_leaf(self, section):
        if section.is_leaf():
            return section
        return self.get_last_leaf(list(section.get_children())[-1])

    def as_dict(self):
        return dict(name=self.name,
                    base_url=self.base_url,
                    sections=[self.get_root().as_dict()])

    def add_section_from_dict(self, d):
        s = Section.add_root(label="Root", slug="", hierarchy=self)
        for pb in d.get('pageblocks', []):
            s.add_pageblock_from_dict(pb)
        for c in d.get('children', []):
            s.add_child_section_from_dict(c)
        return s

    @classmethod
    def from_dict(cls, d):
        h = Hierarchy.objects.create(name=d.get('name', ''),
                                     base_url=d.get('base_url', '/'))
        for s in d.get('sections', []):
            h.add_section_from_dict(s)
        return h

    def get_user_location(self, user):
        if user.is_anonymous():
            return "/"
        (ul, created) = UserLocation.objects.get_or_create(
            user=user,
            hierarchy=self)
        return ul.path

    def get_user_section(self, user):
        location = self.get_user_location(user)[len(self.base_url):]
        return self.find_section_from_path(location)

    def user_visit(self, user, section):
        path = section.get_absolute_url()
        (ul, created) = UserLocation.objects.get_or_create(
            user=user,
            hierarchy=self)
        ul.path = path
        ul.save()


class Section(MP_Node):
    label = models.CharField(max_length=256)
    slug = models.SlugField()
    hierarchy = models.ForeignKey(Hierarchy)
    show_toc = models.BooleanField(
        default=False,
        help_text=("list table of contents of "
                   "immediate child sections (if applicable)"))
    deep_toc = models.BooleanField(
        default=False,
        help_text=("include children of children in TOC. "
                   "(this only makes sense if the above is checked)"))

    def enforce_slug(self):
        # root node gets an empty slug
        if self.is_root():
            self.slug = ""
        # but no other section should ever be able to
        self.slug = slugify(self.slug)[:50]
        if self.slug == "":
            self.slug = slugify(self.label)[:50]
        if self.slug == "":
            # label is empty too, so we need to fall way back
            self.slug = "section-%d" % self.id
        # enforce uniqueness at this section's level in the
        # tree. ie, don't allow two siblings to have the same slug.
        # duplicate slugs at different levels of the tree are fine.
        if not self.is_root():
            # need to make sure no other siblings have the same slug
            while self.slug in self.get_sibling_slugs():
                self.slug = self.slug + "-%d" % self.id

        # TODO: this should maybe go on a save hook to make sure
        # it is always enforced.
        self.save()

    def clear_caches(self):
        cache.delete("pagetree.%d.get_absolute_url" % self.id)
        cache.delete("pagetree.%d.is_last_child" % self.id)
        cache.delete("pagetree.%d.get_edit_url" % self.id)

    def clear_tree_cache(self):
        depth_first_traversal = self.get_root().get_annotated_list()
        for (s, ai) in depth_first_traversal:
            s.clear_caches()
        statsd.incr("pagetree.cache_cleared")

    def get_sibling_slugs(self):
        return [s.slug for s in self.get_siblings() if s != self]

    def get_module(self):
        """ get the top level module that the section is in"""
        if self.is_root():
            return None
        if self.depth == 2:
            return self
        return self.get_ancestors()[1]

    def is_first_child(self):
        return self.get_first_sibling().id == self.id

    def is_last_child(self):
        key = "pagetree.%d.is_last_child" % self.id
        v = cache.get(key)
        if v:
            statsd.incr("pagetree.is_last_child.cache_hit")
            return v
        statsd.incr("pagetree.is_last_child.cache_miss")
        v = self._is_last_child()
        cache.set(key, v)
        return v

    def _is_last_child(self):
        return self.get_last_sibling().id == self.id

    def closing_children(self):
        """ this returns the list of adjacent last children.
        we need this to know how many levels deep need to be closed
        when making the menus as flattened nested lists.
        look for 'closing_children' in a menu.html in a project
        that uses pagetree to see exactly what i mean. """

        s = self
        while not s.is_root() and s.is_last_child():
            yield s
            s = s.get_parent()

    def get_previous(self):
        # previous node in the depth-first traversal
        depth_first_traversal = self.get_root().get_annotated_list()
        for (i, (s, ai)) in enumerate(depth_first_traversal):
            if s.id == self.id:
                # make sure we don't return the root
                if i > 1 and not depth_first_traversal[i - 1][0].is_root():
                    return depth_first_traversal[i - 1][0]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def get_next(self):
        # next node in the depth-first traversal
        depth_first_traversal = self.get_root().get_annotated_list()
        for (i, (s, ai)) in enumerate(depth_first_traversal):
            if s.id == self.id:
                if i < len(depth_first_traversal) - 1:
                    return depth_first_traversal[i + 1][0]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def append_child(self, label, slug='', show_toc=False, deep_toc=False):
        if slug == '':
            slug = slugify(label)
        self.save()
        c = self.add_child(label=label, slug=slug, hierarchy=self.hierarchy,
                           show_toc=show_toc, deep_toc=deep_toc)
        c.enforce_slug()
        return c

    def append_pageblock(self, label, css_extra, content_object):
        neword = self.pageblock_set.count() + 1
        return PageBlock.objects.create(section=self, label=label,
                                        ordinality=neword,
                                        css_extra=css_extra,
                                        content_object=content_object)

    def __unicode__(self):
        return self.label

    def get_absolute_url(self):
        key = "pagetree.%d.get_absolute_url" % self.id
        v = cache.get(key)
        if v:
            statsd.incr("pagetree.get_absolute_url.cache_hit")
            return v
        statsd.incr("pagetree.get_absolute_url.cache_miss")
        v = self._get_absolute_url()
        cache.set(key, v)
        return v

    def _get_absolute_url(self):
        ancestors = self.get_ancestors()
        slugs = [a.slug for a in ancestors[1:]]
        if len(slugs) == 0:
            return self.hierarchy.get_absolute_url() + self.slug + "/"
        url = (self.hierarchy.get_absolute_url() + "/".join(slugs)
               + "/" + self.slug + "/")
        return url

    def get_edit_url(self):
        key = "pagetree.%d.get_edit_url" % self.id
        v = cache.get(key)
        if v:
            statsd.incr("pagetree.get_edit_url.cache_hit")
            return v
        statsd.incr("pagetree.get_edit_url.cache_miss")
        v = self._get_edit_url()
        cache.set(key, v)
        return v

    def _get_edit_url(self):
        ancestors = self.get_ancestors()
        slugs = [a.slug for a in ancestors[1:]]
        if len(slugs) == 0:
            return (
                self.hierarchy.get_absolute_url() + "edit/" + self.slug + "/")
        url = (self.hierarchy.get_absolute_url() + "edit/" + "/".join(slugs)
               + "/" + self.slug + "/")
        return url

    def get_instructor_url(self):
        if self.is_root():
            return self.hierarchy.get_absolute_url() + "instructor/"
        return self.get_parent().get_instructor_url() + self.slug + "/"

    def get_path(self):
        """ same as get_absolute_url, without the leading /"""
        return self.get_absolute_url()[len(self.hierarchy.base_url):]

    def add_child_section_form(self):
        class AddChildSectionForm(forms.Form):
            label = forms.CharField()

        return AddChildSectionForm()

    def renumber_pageblocks(self):
        i = 1
        for block in self.pageblock_set.all():
            block.ordinality = i
            block.save()
            i += 1

    def edit_form(self):
        class EditSectionForm(forms.Form):
            label = forms.CharField(initial=self.label)
            slug = forms.CharField(initial=self.slug)
            show_toc = forms.BooleanField(
                initial=self.show_toc,
                label="Show Table of Contents",
                help_text=("list table of contents of "
                           "immediate child sections (if applicable)"))
            deep_toc = forms.BooleanField(
                initial=self.deep_toc,
                label="Show Deep Table of Contents",
                help_text=(
                    "include children of children (etc) in TOC. "
                    "(this only makes sense if the above is enabled)"))
        return EditSectionForm()

    def move_form(self):
        return MoveNodeForm(instance=self)

    def update_children_order(self, children_ids):
        """children_ids is a list of Section ids for the children
        in the order that they should be set to.

        use with caution. if the ids in children_ids don't match up
        right it will break or do strange things.
        """
        for section_id in children_ids:
            s = Section.objects.get(id=section_id)
            p = s.get_parent()
            s.move(p, pos="last-child")
        self.clear_tree_cache()
        return

    def update_pageblocks_order(self, pageblock_ids):
        """pageblock_ids is a list of PageBlock ids for the children
        in the order that they should be set to.

        use with caution. if the ids in pageblock_ids don't match up
        right it will break or do strange things.
        """
        for (i, id) in enumerate(pageblock_ids):
            sc = PageBlock.objects.get(id=id)
            sc.ordinality = i + 1
            sc.save()

    def available_pageblocks(self):
        return self.hierarchy.available_pageblocks()

    def add_pageblock_form(self):
        class EditForm(forms.Form):
            label = forms.CharField()
            css_extra = forms.CharField(label="extra CSS classes")
        return EditForm()

    def get_first_leaf(self):
        if self.is_leaf():
            return self
        return self.get_children()[0].get_first_leaf()

    def get_last_leaf(self):
        if self.is_leaf():
            return self
        return list(self.get_children())[-1].get_last_leaf()

    def reset(self, user):
        """ clear a user's responses to all pageblocks on this page """
        for p in self.pageblock_set.all():
            if hasattr(p.block(), 'needs_submit'):
                if p.block().needs_submit():
                    p.block().clear_user_submissions(user)

    def submit(self, request_data, user):
        """ store users's responses to the pageblocks on this page """
        proceed = True
        for p in self.pageblock_set.all():
            if hasattr(p.block(), 'needs_submit'):
                if p.block().needs_submit():
                    prefix = "pageblock-%d-" % p.id
                    data = dict()
                    for k in request_data.keys():
                        if k.startswith(prefix):
                            # handle lists for multi-selects
                            v = request_data.getlist(k)
                            if len(v) == 1:
                                data[k[len(prefix):]] = request_data[k]
                            else:
                                data[k[len(prefix):]] = v
                    p.block().submit(user, data)
                    if hasattr(p.block(), 'redirect_to_self_on_submit'):
                        # semi bug here?
                        # proceed will only be set by the last submittable
                        # block on the page. previous ones get ignored.
                        proceed = not p.block().redirect_to_self_on_submit()
        return proceed

    def needs_submit(self):
        """ if any blocks on the page need to be submitted """
        for p in self.pageblock_set.all():
            if hasattr(p.block(), 'needs_submit'):
                if p.block().needs_submit():
                    return True
        return False

    def allow_redo(self, **kwargs):
        """ if any blocks on the page are allowed to be resubmitted """
        for p in self.pageblock_set.all():
            if hasattr(p.block(), 'allow_redo'):
                if hasattr(p.block().allow_redo, '__call__'):
                    if p.block().allow_redo(**kwargs):
                        return True
                else:
                    # not callable, so we expect it
                    # to just be a boolean property
                    if p.block().allow_redo:
                        return True
        return False

    def submitted(self, user):
        """ if all blocks on the page that require submissions
        have been submitted """
        for p in self.pageblock_set.all():
            if hasattr(p.block(), 'needs_submit'):
                if p.block().needs_submit():
                    try:
                        s = p.block().unlocked(user)
                        if not s:
                            # there's an unsubmitted block
                            return False
                    except:
                        # most likely: no unlocked() method
                        pass
        # made it all the way through without any blocks
        # reporting that they are unsubmitted
        return True

    def as_dict(self):
        return dict(
            label=self.label,
            slug=self.slug,
            show_toc=self.show_toc,
            deep_toc=self.deep_toc,
            pageblocks=[b.as_dict() for b in self.pageblock_set.all()],
            children=[s.as_dict() for s in self.get_children()],
        )

    def from_dict(self, d):
        self.label = d.get('label', '')
        self.slug = d.get('slug', '')
        self.show_toc = d.get('show_toc', False)
        self.deep_toc = d.get('deep_toc', False)
        self.save()
        for pb in d.get('pageblocks', []):
            self.add_pageblock_from_dict(pb)
        for c in d.get('children', []):
            self.add_child_section_from_dict(c)

    def add_pageblock_from_dict(self, d):
        blocktype = d.get('block_type', '')
        # now we need to figure out which kind of pageblock to create
        for pb_class in self.available_pageblocks():
            if not pb_class:
                continue
            if pb_class.display_name == blocktype:
                # a match
                if hasattr(pb_class, 'create_from_dict'):
                    block = pb_class.create_from_dict(d)
                    self.append_pageblock(label=d.get('label', ''),
                                          css_extra=d.get('css_extra', ''),
                                          content_object=block)

    def add_child_section_from_dict(self, d):
        s = self.append_child(
            d.get('label', ''), d.get('slug', ''),
            d.get('show_toc', False), d.get('deep_toc', False))
        s.save()
        for pb in d.get('pageblocks', []):
            s.add_pageblock_from_dict(pb)
        for c in d.get('children', []):
            s.add_child_section_from_dict(c)
        self.clear_tree_cache()

    def user_visit(self, user):
        self.hierarchy.user_visit(user, self)

    def user_pagevisit(self, user, status="incomplete"):
        try:
            (upv, created) = UserPageVisit.objects.get_or_create(
                section=self,
                user=user)
        except django.core.exceptions.MultipleObjectsReturned:
            upv = UserPageVisit.objects.filter(
                section=self, user=user).first()
        upv.status = status
        upv.save()

    def get_uservisit(self, user):
        # returns None if the userpagevisit doesn't exist
        return self.userpagevisit_set.filter(user=user).first()

    def save_version(self, user, activity=None, comment=None):
        if not activity:
            activity = ""
        if not comment:
            comment = ""
        json = dumps(self.as_dict())
        v = Version.objects.create(
            section=self,
            user=user,
            data=json,
            activity=activity,
            comment=comment)
        return v
        self.clear_tree_cache()

    def gate_check(self, user):
        """ return bool, section tuple for whether the user
        has visited every section previous to this one and
        which is the first that they need to visit if that's
        not the case """
        if not user:
            # no user: the important thing is just that we deny access
            return False, self

        # otherwise, let's start at the beginning and check each
        depth_first_traversal = self.get_annotated_list(parent=self.get_root())

        # prep a list of all the visits for this user
        upvs = [upv.section.id
                for upv in list(UserPageVisit.objects.filter(user=user))
                if upv.status == 'complete']
        for (i, (s, ai)) in enumerate(depth_first_traversal):
            # skip the root
            if s.is_root():
                continue
            if s.id == self.id:
                # we've reached the current section. That
                # means they're good to go.
                return True, None
            else:
                if s.id not in upvs:
                    # uh oh. found a page that they haven't visited
                    # need to send them there first
                    return False, s
        # went through the entire list of sections without finding
        # the current section?!
        assert False, "current section not found in traversal"


class PageBlock(models.Model):
    section = models.ForeignKey(Section)
    ordinality = models.PositiveIntegerField(default=1)
    label = models.CharField(max_length=256, blank=True, null=True)
    css_extra = models.CharField(
        max_length=256, blank=True, null=True,
        help_text="extra CSS classes (space separated)")

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('section', 'ordinality',)

    def __unicode__(self):
        return "%s [%d]: %s" % (self.section.label, self.ordinality,
                                self.label)

    def block(self):
        return self.content_object

    def edit_label(self):
        """ provide a label for the pageblock to make the
        edit interface easier to read """
        if hasattr(self.block(), 'edit_label'):
            return self.block().edit_label()
        else:
            return self.block().display_name

    def render(self, **kwargs):
        if hasattr(self.content_object, "template_file"):
            t = get_template(getattr(self.content_object, "template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        else:
            return self.content_object.render()

    def render_js(self, **kwargs):
        if hasattr(self.content_object, "js_template_file"):
            t = get_template(getattr(self.content_object, "js_template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        elif hasattr(self.content_object, "js_render"):
            return self.content_object.js_render()
        else:
            return ""

    def render_css(self, **kwargs):
        if hasattr(self.content_object, "css_template_file"):
            t = get_template(getattr(self.content_object, "css_template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        elif hasattr(self.content_object, "css_render"):
            return self.content_object.css_render()
        else:
            return ""

    def render_summary(self, **kwargs):
        if hasattr(self.content_object, "summary_template_file"):
            t = get_template(getattr(self.content_object,
                                     "summary_template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        elif hasattr(self.content_object, "summary_render"):
            return self.content_object.summary_render()
        else:
            return ""

    def default_edit_form(self):
        class EditForm(forms.Form):
            label = forms.CharField(initial=self.label)
            css_extra = forms.CharField(initial=self.css_extra,
                                        label="extra CSS classes")
        return EditForm()

    def edit_form(self):
        return self.content_object.edit_form()

    def edit(self, vals, files):
        self.label = vals.get('label', '')
        self.css_extra = vals.get('css_extra', '')
        self.save()
        self.content_object.edit(vals, files)

    def delete(self):
        section = self.section
        super(PageBlock, self).delete()  # Call the "real" delete() method
        section.renumber_pageblocks()

    def as_dict(self):
        d = dict()
        if hasattr(self.content_object, 'as_dict'):
            d = self.content_object.as_dict()
        d['label'] = self.label
        d['css_extra'] = self.css_extra
        d['block_type'] = self.content_object.display_name
        return d


class UserLocation(models.Model):
    """ last path a given user visited (for a particular hierarchy) """
    user = models.ForeignKey(User)
    hierarchy = models.ForeignKey(Hierarchy)
    path = models.CharField(max_length=256, default="/")

    class Meta:
        unique_together = (('user', 'hierarchy'),)


class UserPageVisit(models.Model):
    """ for detailed tracking """
    user = models.ForeignKey(User)
    section = models.ForeignKey(Section)
    status = models.CharField(max_length=256, default="incomplete")
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user', 'section'),)


class Version(models.Model):
    """ very basic versioning """
    section = models.ForeignKey(Section)
    user = models.ForeignKey(User)
    saved_at = models.DateTimeField(auto_now_add=True)
    activity = models.TextField(default="", blank=True, null=True)
    data = models.TextField(default="", blank=True, null=True)
    comment = models.TextField(default="", blank=True, null=True)

    class Meta:
        ordering = ["-saved_at", ]

    def more_recent_versions(self):
        versions = list(
            self.section.version_set.filter(
                saved_at__gt=self.saved_at))
        for s in self.section.get_descendants():
            for v in s.version_set.filter(saved_at__gt=self.saved_at):
                versions.append(v)
        versions.sort(lambda a, b: cmp(b.saved_at, a.saved_at))
        return versions


class TestReportColumn(ReportColumnInterface):

    def identifier(self):
        return "Test Report Column"

    def metadata(self):
        return ['', self.identifier(), "generic",
                "string", "this is a test"]

    def user_value(self, user):
        return user.username


class TestBlock(models.Model):
    """ this is a pageblock that is exclusively for pagetree's
    internal tests so we have some kind of block to test with
    without having to pull in the whole django-pageblocks
    package and its dependencies.

    You should never use it. In fact, forget that you ever saw this.
    """
    pageblocks = generic.GenericRelation(PageBlock)
    body = models.TextField(blank=True)

    template_file = "pagetree/testblock.html"
    display_name = "Test Block"

    def __unicode__(self):
        return unicode(self.pageblock())

    def pageblock(self):
        return self.pageblocks.first()

    @classmethod
    def add_form(self):
        class AddForm(forms.Form):
            body = forms.CharField(
                widget=forms.widgets.Textarea(attrs={'cols': 80}))
        return AddForm()

    @classmethod
    def create(self, request):
        return TestBlock.objects.create(body=request.POST.get('body', ''))

    @classmethod
    def create_from_dict(self, d):
        return TestBlock.objects.create(body=d.get('body', ''))

    def edit_form(self):
        class EditForm(forms.Form):
            body = forms.CharField(widget=forms.widgets.Textarea(),
                                   initial=self.body)
        return EditForm()

    def edit(self, vals, files):
        self.body = vals.get('body', '')
        self.save()

    def as_dict(self):
        return dict(body=self.body)

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
