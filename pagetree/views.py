from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from pagetree.models import Section, PageBlock

def reorder_pageblocks(request,id):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=id)
    keys = request.GET.keys()
    # TODO: numerical sort order bug in these with, eg, pageblock_id_9, pageblock_id_10
    keys.sort()
    pageblocks = [int(request.GET[k]) for k in keys if k.startswith('pageblock_id_')]
    section.update_pageblocks_order(pageblocks)
    return HttpResponse("ok")

def reorder_section_children(request,id):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section,id=id)
    keys = request.GET.keys()
    keys.sort()
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
