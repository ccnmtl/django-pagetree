from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Context, loader
from pagetree.models import Section, PageBlock
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.core.urlresolvers import reverse
import string

def reorder_pageblocks(request,id):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=id)
    keys = request.GET.keys()
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    pageblocks = [int(request.GET[k]) for k in keys if k.startswith('pageblock_id_')]
    section.update_pageblocks_order(pageblocks)
    return HttpResponse("ok")

def reorder_section_children(request,id):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=id)
    keys = request.GET.keys()
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    children = [int(request.GET[k]) for k in keys if k.startswith('section_id_')]
    section.update_children_order(children)
    return HttpResponse("ok")

def add_childsection(request,section_id):
    parent = get_object_or_404(Section,id=section_id)
    
    if request.method == "POST":
        parent.append_child(request.POST.get('label','unnamed'),
                            request.POST.get('slug','unknown'),
                            request.POST.get('template', ''))
        return HttpResponse('<script type="text/javascript">opener.dismissAddSectionPopup(window);</script>')
    else:
        ctx = Context({'parent': parent, 'title': 'Add Child Section'})
        template = loader.get_template('admin/pagetree/section/add_section.html')
        return HttpResponse(template.render(ctx))
    
def add_pageblock(request, section_id):
    section = get_object_or_404(Section,id=section_id)
    
    if request.method == "POST":
        blocktype = request.POST.get('blocktype','')
        # now we need to figure out which kind of pageblock to create
        for pb_class in section.available_pageblocks():
            if pb_class.display_name == blocktype:
                # a match
                block = pb_class.create(request)
                pageblock = section.append_pageblock(label=request.POST.get('label',''),content_object=block)
        return HttpResponse('<script type="text/javascript">opener.dismissPageBlockPopup(window);</script>')
    else:
        ctx = Context({'section': section, 'title': 'Add Page Block'})
        template = loader.get_template('admin/pagetree/pageblock/add_pageblock.html')
        return HttpResponse(template.render(ctx))
    
def edit_pageblock(request, block_id):
    block = get_object_or_404(PageBlock,id=block_id)
        
    if request.method == "POST":
        block.edit(request.POST,request.FILES)
        if request.POST.has_key('_continue'):
            return HttpResponseRedirect(reverse('edit-pageblock', args=[block.id]))
        else:
            return HttpResponse('<script type="text/javascript">opener.dismissPageBlockPopup(window);</script>')
    else:
        ctx = Context({'pageblock': block, 'title': 'Edit ' + string.capwords(block.content_type.name)})
        template = loader.get_template('admin/pagetree/pageblock/edit_pageblock.html')
        return HttpResponse(template.render(ctx))


