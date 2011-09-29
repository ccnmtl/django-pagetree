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
from treebeard.mp_tree import MP_Node

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
            return Section.objects.get(hierarchy=self,label="Root").get_root()
        except Section.DoesNotExist:
            return Section.add_root(label="Root",slug="",hierarchy=self)

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

class Section(MP_Node):
    label = models.CharField(max_length=256)
    slug = models.SlugField()
    hierarchy = models.ForeignKey(Hierarchy)

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
        for (i,(s,ai)) in enumerate(depth_first_traversal):
            if s.id == self.id:
                # make sure we don't return the root
                if i > 1 and not depth_first_traversal[i-1][0].is_root():
                    return depth_first_traversal[i-1][0]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def get_next(self):
        # next node in the depth-first traversal
        depth_first_traversal = self.get_root().get_annotated_list()
        for (i,(s,ai)) in enumerate(depth_first_traversal):
            if s.id == self.id:
                if i < len(depth_first_traversal) - 1:
                    return depth_first_traversal[i+1][0]
                else:
                    return None
        # made it through without finding ourselves? weird.
        return None

    def append_child(self,label,slug=''):
        if slug == '':
            slug = slugify(label)
        return self.add_child(label=label,slug=slug,hierarchy=self.hierarchy)

    def append_pageblock(self,label,content_object):
        neword = self.pageblock_set.count() + 1
        return PageBlock.objects.create(section=self,label=label,ordinality=neword,content_object=content_object)

    def __unicode__(self):
        return self.label

    def get_absolute_url(self):
        if self.is_root():
            return self.hierarchy.get_absolute_url()
        return self.get_parent().get_absolute_url() + self.slug + "/"

    def get_path(self):
        """ same as get_absolute_url, without the leading /"""
        return self.get_absolute_url()[1:]

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
        for section_id in children_ids:
            s = Section.objects.get(id=section_id)
            p = s.get_parent()
            s.move(p,pos="last-child")
        return 

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

    def reset(self,user):
        """ clear a user's responses to all pageblocks on this page """
        for p in self.pageblock_set.all():
            if hasattr(p.block(),'needs_submit'):
                if p.block().needs_submit():
                    p.block().clear_user_submissions(user)

    def submit(self,request_data,user):
        """ store users's responses to the pageblocks on this page """
        proceed = True
        for p in self.pageblock_set.all():
            if hasattr(p.block(),'needs_submit'):
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
                    p.block().submit(user,data)
                    if hasattr(p.block(),'redirect_to_self_on_submit'):
                        # semi bug here?
                        # proceed will only be set by the last submittable
                        # block on the page. previous ones get ignored.
                        proceed = not p.block().redirect_to_self_on_submit()
        return proceed

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

    def edit_label(self):
        """ provide a label for the pageblock to make the edit interface easier to read """
        if hasattr(self.block(),'edit_label'):
            return self.block().edit_label()
        else:
            return self.block().display_name

    def render(self,**kwargs):
        if hasattr(self.content_object,"template_file"):
            t = get_template(getattr(self.content_object,"template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        else:
            return self.content_object.render()

    def render_js(self,**kwargs):
        if hasattr(self.content_object,"js_template_file"):
            t = get_template(getattr(self.content_object,"js_template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        elif hasattr(self.content_object,"js_render"):
            return self.content_object.js_render()
        else:
            return ""

    def render_css(self,**kwargs):
        if hasattr(self.content_object,"css_template_file"):
            t = get_template(getattr(self.content_object,"css_template_file"))
            d = kwargs
            d['block'] = self.content_object
            c = Context(d)
            return t.render(c)
        elif hasattr(self.content_object,"css_render"):
            return self.content_object.css_render()
        else:
            return ""


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
        
    def delete(self):
         section = self.section
         super(PageBlock, self).delete() # Call the "real" delete() method
         section.renumber_pageblocks()
        
