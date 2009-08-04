from django.conf import settings
from django.db import models
from django import forms
from django.template import Template,Context
from django.template.loader import get_template
from django.http import Http404


class Hierarchy(models.Model):
    name = models.CharField(max_length=256)
    base_url = models.CharField(max_length=256,default="")

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

    def depth(self):
        """ return count of how deep in the hierarchy this section is """
        if self.is_root:
            return 0
        else:
            return self.get_parent().depth() + 1

    def is_first_child(self):
        return SectionChildren.objects.filter(parent=self.get_parent(),ordinality__lt=self.get_ordinality()).count() == 0

    def is_last_child(self):
        return SectionChildren.objects.filter(parent=self.get_parent(),ordinality__gt=self.get_ordinality()).count() == 0

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
        l = [self]
        for c in self.get_children():
            l.extend(c.get_descendents())
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

    def append_child(self,label,slug):
        ns = Section.objects.create(hierarchy=self.hierarchy,
                                    label=label,slug=slug,is_root=False)
        neword = SectionChildren.objects.filter(parent=self).count() + 1
        nsc = SectionChildren.objects.create(parent=self,child=ns,ordinality=neword)
        return ns

    def append_pageblock(self,label):
        neword = self.pageblock_set.count() + 1
        return PageBlock.objects.create(section=self,label=label,ordinality=neword)

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
            slug = forms.CharField()
        return AddChildSectionForm()

    def renumber_pageblocks(self):
        i = 1
        for block in self.pageblock_set.all():
            block.ordinality = i
            block.save()
            i += 1
            

class SectionChildren(models.Model):
    parent = models.ForeignKey(Section,related_name="parent")
    child = models.ForeignKey(Section,related_name="child")
    ordinality = models.IntegerField(default=1)

    class Meta:
        ordering = ('ordinality',)

class PageBlock(models.Model):
    section = models.ForeignKey(Section)
    ordinality = models.IntegerField(default=1)
    label = models.CharField(max_length=256)

    class Meta:
        ordering = ('section','ordinality',)

    def _load_block_object(self,path):
        i = path.rfind('.')
        module, attr = path[:i], path[i+1:]
        try:
            mod = __import__(module, {}, {}, [attr])
        except ImportError, e:
            raise ImproperlyConfigured, 'Error importing pagetree pageblock class %s: "%s"' % (module, e)
        except ValueError, e:
            raise ImproperlyConfigured, 'Error importing pagetree pagebock class. '
        try:
            cls = getattr(mod, attr)
        except AttributeError:
            raise ImproperlyConfigured, 'Module "%s" does not define a "%s" pageblock class' % (module, attr)
        return cls

    def block(self):
        if hasattr(settings,'PAGETREE_PAGEBLOCK_CLASSES'):
            for pb in getattr(settings,'PAGETREE_PAGEBLOCK_CLASSES'):
                pbc = self._load_block_object(pb)
                r = pbc.objects.filter(pageblock=self)
                if r.count() > 0:
                    return r[0]
        # no matches
        return None

    def render(self,**kwargs):
        pb = self.block()
        if hasattr(pb,"template_file"):
            t = get_template(getattr(pb,"template_file"))
            d = kwargs
            d['block'] = pb
            c = Context(d)
            return t.render(c)
        else:
            return pb.render()

    def default_edit_form(self):
        class EditForm(forms.Form):
            label = forms.CharField(initial=self.label)
        return EditForm()

    def edit_form(self):
        return self.block().edit_form()

    def edit(self,vals):
        self.label = vals.get('label','')
        self.save()
        self.block().edit(vals)
        
        
