from django.db import models
from django import forms
from django.template import Context
from django.template.loader import get_template
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import get_model
from django.core.cache import cache
from django.template.defaultfilters import slugify

settings = None
try:
    import settings
except:
    # if we can't import settings, it just means
    # they won't be able to get a list of available
    # pageblock classes
    settings = None
 

class Hierarchy(models.Model):
    name = models.CharField(max_length=256)
    base_url = models.CharField(max_length=256,default="")

    @staticmethod
    def get_hierarchy(name):
        return Hierarchy.objects.get_or_create(name=name,defaults=dict(base_url="/"))[0]

    def get_absolute_url(self):
        return self.base_url

    def __unicode__(self):
        return self.name

    def get_root(self):
        # will create it if it doesn't exist
        try:
            return Section.objects.get(hierarchy=self,is_root=True)
        except Section.DoesNotExist:
            return Section.objects.create(label="Root",slug="",hierarchy=self,
                                          is_root=True)

    def get_top_level(self):
        return self.get_root().get_children()

    def get_section_from_path(self,path):
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
            if slugs.has_key(slug):
                current = slugs[slug]
            else:
                raise Http404()
        return current

    def available_pageblocks(self):
        if hasattr(settings,'PAGEBLOCKS'):
            return [get_model(*pb.split('.')) for pb in settings.PAGEBLOCKS]
        else:
            return []

    def get_first_leaf(self,section):
        if (section.is_leaf()):
            return section
    
        return self.get_first_leaf(section.get_children()[0])

    def get_last_leaf(self,section):
        if (section.is_leaf()):
            return section
    
        return self.get_last_leaf(section.get_children()[-1])

class Section(models.Model):
    label = models.CharField(max_length=256)
    slug = models.SlugField()
    hierarchy = models.ForeignKey(Hierarchy)
    # every hierarchy should have a root section
    # it never gets displayed. just exists to be a parent
    # to the top_level sections.
    is_root = models.BooleanField(default=False)

    def get_root(self):
        if self.is_root:
            return self
        else:
            return self.get_parent().get_root()

    def get_module(self):
        """ get the top level module that the section is in"""
        if self.is_root:
            return None
        return self.get_ancestors()[1]

    def depth(self):
        """ return count of how deep in the hierarchy this section is """
        if self.is_root:
            return 0
        else:
            return self.get_parent().depth() + 1

    def get_ancestors(self,acc=None):
        if acc is None:
            acc = []
        acc = [self] + acc
        if self.is_root:
            return acc
        else:
            return self.get_parent().get_ancestors(acc)

    def is_first_child(self):
        return SectionChildren.objects.filter(parent=self.get_parent(),ordinality__lt=self.get_ordinality()).count() == 0

    def is_last_child(self):
        return SectionChildren.objects.filter(parent=self.get_parent(),ordinality__gt=self.get_ordinality()).count() == 0

    def closing_children(self):
        """ this returns the list of adjacent last children.
        we need this to know how many levels deep need to be closed
        when making the menus as flattened nested lists. 
        look for 'closing_children' in a menu.html in a project
        that uses pagetree to see exactly what i mean. """

        s = self
        while not s.is_root and s.is_last_child():
            yield s
            s = s.get_parent()

    def get_ordinality(self):
        if self.is_root:
            return -1
        return SectionChildren.objects.get(parent=self.get_parent(),child=self).ordinality

    def get_children(self):
        return [sc.child for sc in SectionChildren.objects.filter(parent=self).order_by("ordinality")]

    def get_parent(self):
        if self.is_root:
            return None
        return SectionChildren.objects.filter(child=self)[0].parent

    def get_descendents(self):
        """ returns flattened depth-first traversal of this section and its children """
        # quick/dirty memorize
        try:
            descendents = cache.get("descendents_%d" % self.id)
            if descendents:
                return descendents
        except KeyError:
            pass

        l = [self]
        for c in self.get_children():
            l.extend(c.get_descendents())
        # just cache it for 1 second. The idea is to make
        # repeated calls fast, but not have to worry much about
        # dirtying the cache
        cache.set("descendents_%d" % self.id,l,1)
        return l


    def get_previous(self):
        depth_first_traversal = self.get_root().get_descendents() 
        for (i,s) in enumerate(depth_first_traversal):
            if s.id == self.id:
                # first element is the root, so we don't want to
                # return that
                if i > 1:
                    return depth_first_traversal[i-1]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def get_previous_leaf(self):
        depth_first_traversal = self.get_root().get_descendents()
        for (i,s) in enumerate(depth_first_traversal):
            if s.id == self.id:
                # first element is the root, so we don't want to
                # return that
                prev = None
                while i > 1 and not prev:
                    node = depth_first_traversal[i-1]
                    if node and len(node.get_children()) > 0:
                        i -= 1
                    else:
                        prev = node
                return prev
        # made it through without finding ourselves? weird.
        return None

    def get_next(self):
        depth_first_traversal = self.get_root().get_descendents() 
        for (i,s) in enumerate(depth_first_traversal):
            if s.id == self.id:
                if i < len(depth_first_traversal) - 1:
                    return depth_first_traversal[i+1]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def get_siblings(self):
        return [sc.child for sc in SectionChildren.objects.filter(parent=self.get_parent())]

    def is_leaf(self):
        return SectionChildren.objects.filter(parent=self).count() == 0

    def append_child(self,label,slug=''):
        if slug == '':
            slug = slugify(label)
        ns = Section.objects.create(hierarchy=self.hierarchy,
                                    label=label,slug=slug,is_root=False)
        neword = SectionChildren.objects.filter(parent=self).count() + 1
        nsc = SectionChildren.objects.create(parent=self,child=ns,ordinality=neword)
        return ns

    def append_pageblock(self,label,content_object):
        neword = self.pageblock_set.count() + 1
        return PageBlock.objects.create(section=self,label=label,ordinality=neword,content_object=content_object)

    def insert_child(self,child,position):
        pass

    def __unicode__(self):
        return self.label

    def get_absolute_url(self):
        if self.is_root:
            return self.hierarchy.get_absolute_url()
        return self.get_parent().get_absolute_url() + self.slug + "/"

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
        return EditSectionForm()

    def update_children_order(self,children_ids):
        """children_ids is a list of Section ids for the children
        in the order that they should be set to.

        use with caution. if the ids in children_ids don't match up
        right it will break or do strange things.
        """
        for (i,id) in enumerate(children_ids):
            sc = SectionChildren.objects.get(parent=self,child__id=id)
            sc.ordinality = i + 1
            sc.save()

    def update_pageblocks_order(self,pageblock_ids):
        """pageblock_ids is a list of PageBlock ids for the children
        in the order that they should be set to.

        use with caution. if the ids in pageblock_ids don't match up
        right it will break or do strange things.
        """
        for (i,id) in enumerate(pageblock_ids):
            sc = PageBlock.objects.get(id=id)
            sc.ordinality = i + 1
            sc.save()

    def available_pageblocks(self):
        return self.hierarchy.available_pageblocks()
    def add_pageblock_form(self):
        class EditForm(forms.Form):
            label = forms.CharField()
        return EditForm()
    def get_first_leaf(self):
        if (self.is_leaf()):
            return self
    
        return self.get_children()[0].get_first_leaf()

    def get_last_leaf(self):
        if (self.is_leaf()):
            return self
    
        return self.get_children()[-1].get_last_leaf()

class SectionChildren(models.Model):
    parent = models.ForeignKey(Section,related_name="parent")
    child = models.ForeignKey(Section,related_name="child")
    ordinality = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ('ordinality',)

    def __unicode__(self):
        return "%s -> [%d] %s" % (self.parent.label,self.ordinality,self.child.label)

class PageBlock(models.Model):
    section = models.ForeignKey(Section)
    ordinality = models.PositiveIntegerField(default=1)
    label = models.CharField(max_length=256, blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('section','ordinality',)

    def __unicode__(self):
        return "%s [%d]: %s" % (self.section.label,self.ordinality,self.label)

    def block(self):
        return self.content_object

    def render(self,**kwargs):
        if hasattr(self.content_object,"template_file"):
            t = get_template(getattr(self.content_object,"template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        else:
            return self.content_object.render()

    def default_edit_form(self):
        class EditForm(forms.Form):
            label = forms.CharField(initial=self.label)
        return EditForm()

    def edit_form(self):
        return self.content_object.edit_form()

    def edit(self,vals,files):
        self.label = vals.get('label','')
        self.save()
        self.content_object.edit(vals,files)
        
