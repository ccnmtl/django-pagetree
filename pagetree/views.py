from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from pagetree.models import Section, PageBlock
from django.template.defaultfilters import slugify

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

def delete_pageblock(request,id):
    block = get_object_or_404(PageBlock,id=id)
    section = block.section
    block.block().delete()
    block.delete()
    section.renumber_pageblocks()
    return HttpResponseRedirect("/edit" + section.get_absolute_url())

def edit_pageblock(request,id):
    block = get_object_or_404(PageBlock,id=id)
    section = block.section
    block.edit(request.POST,request.FILES)
    return HttpResponseRedirect("/edit" + section.get_absolute_url())

def edit_section(request,id):
    section = get_object_or_404(Section,id=id)
    section.label = request.POST.get('label','')
    section.slug = request.POST.get('slug',slugify(section.label))
    section.save()
    return HttpResponseRedirect("/edit" + section.get_absolute_url())

def delete_section(request,id):
    section = get_object_or_404(Section,id=id)
    if request.method == "POST":
        parent = section.get_parent()
        section.delete()
        return HttpResponseRedirect("/edit" + parent.get_absolute_url())
    return HttpResponse("""
<html><body><form action="." method="post">Are you Sure?
<input type="submit" value="Yes, delete it" /></form></body></html>
""")

def add_pageblock(request,id):
    section = get_object_or_404(Section,id=id)
    blocktype = request.POST.get('blocktype','')
    # now we need to figure out which kind of pageblock to create
    for pb_class in section.available_pageblocks():
        if pb_class.display_name == blocktype:
            # a match
            block = pb_class.create(request)
            pageblock = section.append_pageblock(label=request.POST.get('label',''),content_object=block)
    return HttpResponseRedirect("/edit" + section.get_absolute_url())
