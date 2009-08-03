from django.conf import settings
from django.db import models
from django import forms
from django.template import Template,Context
from django.template.loader import get_template


class Hierarchy(models.Model):
    name = models.CharField(max_length=256)
    base_url = models.CharField(max_length=256,default="")

    def get_absolute_url(self):
        return self.base_url

    def __unicode__(self):
        return self.name

    def get_root(self):
        try:
            return Section.objects.get(hierarchy=self,is_root=True)
        except Section.DoesNotExist:
            return Section.objects.create(label="Root",slug="",hierarchy=self,
                                          is_root=True)

    def get_top_level(self):
        return self.get_root().get_children()

    def menu(self):
        return [c.menu() for c in self.get_top_level()]

    def as_ul(self):
        return [c.as_ul() for c in self.get_top_level()]

def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

class Section(models.Model):
    label = models.CharField(max_length=256)
    slug = models.SlugField()
    hierarchy = models.ForeignKey(Hierarchy)
    # every hierarchy should have a root section
    # it never gets displayed. just exists to be a parent
    # to the top_level sections.
    is_root = models.BooleanField(default=False)

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

    def as_ul(self,**kwargs):
        t = get_template("pagetree/section_ul.html")
        d = kwargs
        d['section'] = self
        c = Context(d)
        return t.render(c)

    def as_edit_ul(self,**kwargs):
        t = get_template("pagetree/section_edit_ul.html")
        d = kwargs
        d['s'] = self
        c = Context(d)
        return t.render(c)

    def menu(self):
        return dict(s=self,children=[c.menu() for c in self.get_children()])

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

    def get_next(self):
        if self.is_leaf():
            if self.is_root:
                # leaf and root? only one section in the tree
                return None
            # get next sibling
            next_siblings = SectionChildren.objects.filter(parent=self.get_parent())
            if next_siblings.count() > 0:
                return next_siblings[0].child
            else:
                # no next siblings at this level, so return the parent's
                # next.
                parent = self.get_parent()
                if parent is not None:
                    return parent.get_next()
                else:
                    # no more next siblings and no parent?
                    # we're at the end.
                    return None
        else:
            # has children, so go to the first child
            return self.get_children()[0]

    def get_siblings(self):
        return [sc.child for sc in SectionChildren.objects.filter(parent=self.get_parent())]

    def get_prev(self):
        pass

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

    def _get_block_object(self):
        if hasattr(settings,'PAGETREE_PAGEBLOCK_CLASSES'):
            print "hasattr"
            for pb in getattr(settings,'PAGETREE_PAGEBLOCK_CLASSES'):
                pbc = self._load_block_object(pb)
                r = pbc.objects.filter(pageblock=self)
                if r.count() > 0:
                    print "none for %s" % pb
                    return r[0]
        # no matches
        return None

    def render(self,**kwargs):
        pb = self._get_block_object()
        if hasattr(pb,"template_file"):
            t = get_template(getattr(pb,"template_file"))
            d = kwargs
            d['block'] = pb
            c = Context(d)
            return t.render(c)
        else:
            return pb.render()
            
        
