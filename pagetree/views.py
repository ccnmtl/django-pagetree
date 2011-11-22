from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Context, loader
from pagetree.models import Section, PageBlock
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.core.urlresolvers import reverse
import string
from pagetree.helpers import get_section_from_path
from django.shortcuts import render_to_response


def reorder_pageblocks(request,section_id,id_prefix="pageblock_id_"):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=section_id)
    keys = request.GET.keys()
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    pageblocks = [int(request.GET[k]) for k in keys if k.startswith(id_prefix)]
    section.update_pageblocks_order(pageblocks)
    return HttpResponse("ok")

def reorder_section_children(request,section_id,id_prefix="section_id_"):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=section_id)
    keys = request.GET.keys()
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    children = [int(request.GET[k]) for k in keys if k.startswith(id_prefix)]
    section.update_children_order(children)
    return HttpResponse("ok")

def delete_pageblock(request,pageblock_id,success_url=None):
    block = get_object_or_404(PageBlock,id=pageblock_id)
    section = block.section
    try:
        block.block().delete()
    except AttributeError:
        # if the model has been refactored, we sometimes
        # end up with 'stub' pageblocks floating around
        # that no longer have a block object associated
        # it's nice to still be able to delete them
        # without having to scrap the whole db and start over
        pass
    block.delete()
    if success_url is None:
        success_url = "/edit" + section.get_absolute_url()
    return HttpResponseRedirect(success_url)

def export_pageblock_json(request,pageblock_id):
    block = get_object_or_404(PageBlock,id=pageblock_id)
    json = simplejson.dumps(block.block().as_dict())
    r = HttpResponse(json,mimetype="application/json")
    r['Content-Disposition'] = 'attachment; filename=pageblock_%d.json' % int(pageblock_id)
    return r

def import_pageblock_json(request,pageblock_id):
    block = get_object_or_404(PageBlock,id=pageblock_id)
    if request.method == "POST":
        if not request.FILES.has_key('file'):
            return HttpResponse("you must upload a json file")
        json = simplejson.loads(request.FILES['file'].read())
        block.block().import_from_dict(json)
        return HttpResponseRedirect("/edit" + block.section.get_absolute_url())
    else:
        return render_to_response("import_json.html",dict())

def edit_pageblock(request,pageblock_id,success_url=None):
    block = get_object_or_404(PageBlock,id=pageblock_id)
    section = block.section
    block.edit(request.POST,request.FILES)
    if success_url is None:
        success_url = "/edit" + section.get_absolute_url()
    return HttpResponseRedirect(success_url)

def edit_section(request,section_id,success_url=None):
    section = get_object_or_404(Section,id=section_id)
    section.label = request.POST.get('label','')
    section.slug = request.POST.get('slug',slugify(section.label))
    section.save()
    if success_url is None:
        success_url = "/edit" + section.get_absolute_url()
    return HttpResponseRedirect(success_url)

def delete_section(request,section_id,success_url=None):
    section = get_object_or_404(Section,id=section_id)
    if request.method == "POST":
        parent = section.get_parent()
        section.delete()
        if success_url is None:
            success_url = "/edit" + parent.get_absolute_url()
        return HttpResponseRedirect(success_url)
    return HttpResponse("""
<html><body><form action="." method="post">Are you Sure?
<input type="submit" value="Yes, delete it" /></form></body></html>
""")

def add_pageblock(request,section_id,success_url=None):
    section = get_object_or_404(Section,id=section_id)
    blocktype = request.POST.get('blocktype','')
    # now we need to figure out which kind of pageblock to create
    for pb_class in section.available_pageblocks():
        if pb_class.display_name == blocktype:
            # a match
            block = pb_class.create(request)
            pageblock = section.append_pageblock(label=request.POST.get('label',''),content_object=block)
    if success_url is None:
        success_url = "/edit" + section.get_absolute_url()
    return HttpResponseRedirect(success_url)

def add_child_section(request,section_id,success_url=None):
    section = get_object_or_404(Section,id=section_id)
    child = section.append_child(request.POST.get('label','unnamed'),
                                 request.POST.get('slug',''))
    if success_url is None:
        success_url = "/edit" + section.get_absolute_url()
    return HttpResponseRedirect(success_url)

def create_tree_root(request):
    section = get_section_from_path("") # creates a root if one doesn't exist
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

from treebeard.forms import MoveNodeForm
def move_section(request, section_id):
    section = get_object_or_404(Section,id=section_id)
    
    if request.method == 'POST': # If the form has been submitted...
        form = MoveNodeForm(request.POST, instance=section) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            to_section = get_object_or_404(Section,id=form.cleaned_data['_ref_node_id'])
            position = form.cleaned_data['_position']
            section.move(to_section, position)
        
            redirect = '/admin/pagetree/section/%s' % (section.id)
            return HttpResponseRedirect(redirect) # Redirect after POST
    else:
        form = MoveNodeForm(instance=section) # An unbound form
        
    return render_to_response('movenodeform.html', { 'form': form, 'instance': section, 'app_label': 'Pagetree' })
