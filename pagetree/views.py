from django.http import HttpResponse
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
