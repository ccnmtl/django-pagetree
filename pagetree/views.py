from __future__ import unicode_literals

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from json import dumps, loads
from pagetree.helpers import get_section_from_path
from pagetree.forms import MoveSectionForm
from pagetree.models import Section, PageBlock, Hierarchy, Version


def reorder_pageblocks(request, section_id, id_prefix="pageblock_id_"):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section, id=section_id)
    section.save_version(request.user, activity="reorder pageblocks")
    keys = list(request.GET)
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    pageblocks = [int(request.GET[k]) for k in keys if k.startswith(id_prefix)]
    section.update_pageblocks_order(pageblocks)
    return HttpResponse("ok")


def reorder_section_children(request, section_id, id_prefix="section_id_"):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section, id=section_id)
    section.save_version(request.user, activity="reorder children")
    keys = list(request.GET)
    keys.sort(key=lambda x: int(x.split('_')[-1]))
    children = [int(request.GET[k]) for k in keys if k.startswith(id_prefix)]
    section.update_children_order(children)
    section.clear_tree_cache()
    return HttpResponse("ok")


def delete_pageblock(request, pageblock_id, success_url=None):
    block = get_object_or_404(PageBlock, id=pageblock_id)
    if request.method == "POST":
        section = block.section
        section.save_version(request.user,
                             activity="delete block [%s]" % smart_str(block))
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
            success_url = section.get_edit_url()
        return HttpResponseRedirect(success_url)
    return TemplateResponse(request, 'delete_confirm.html')


def export_pageblock_json(request, pageblock_id):
    block = get_object_or_404(PageBlock, id=pageblock_id)
    the_json = dumps(block.as_dict())
    r = HttpResponse(the_json, content_type="application/json")
    r['Content-Disposition'] = ('attachment; filename=pageblock_%d.json'
                                % int(pageblock_id))
    return r


def import_pageblock_json(request, pageblock_id):
    block = get_object_or_404(PageBlock, id=pageblock_id)
    block.section.save_version(
        request.user,
        activity="importing pageblock json [%s]" % smart_str(block))
    if request.method == "POST":
        if 'file' not in request.FILES:
            return HttpResponse("you must upload a json file")
        json = loads(request.FILES['file'].read())
        block.import_from_dict(json)
        return HttpResponseRedirect(block.section.get_edit_url())
    else:
        return render(request, "import_json.html")


def edit_pageblock(request, pageblock_id, success_url=None):
    block = get_object_or_404(PageBlock, id=pageblock_id)
    section = block.section
    section.save_version(
        request.user,
        activity="edit pageblock [%s]" % smart_str(block))
    block.edit(request.POST, request.FILES)
    if success_url is None:
        success_url = section.get_edit_url()
    return HttpResponseRedirect(success_url)


def edit_section(request, section_id, success_url=None):
    section = get_object_or_404(Section, id=section_id)
    section.save_version(request.user, activity="edit section")
    section.label = request.POST.get('label', '')
    section.slug = slugify(request.POST.get('slug', section.label))[:50]

    value = request.POST.get('show_toc', False)
    section.show_toc = value in ('True', True, 'on')

    value = request.POST.get('deep_toc', False)
    section.deep_toc = value in ('True', True, 'on')

    section.save()
    section.enforce_slug()
    section.save()
    section.clear_caches()
    if success_url is None:
        success_url = section.get_edit_url()
    return HttpResponseRedirect(success_url)


def delete_section(request, section_id, success_url=None):
    section = get_object_or_404(Section, id=section_id)
    if request.method == "POST":
        parent = section.get_parent()
        if parent:
            parent.save_version(
                request.user,
                activity="delete child section [%s]" % smart_str(section))
        section.delete()
        if success_url is None:
            if parent:
                parent.clear_tree_cache()
                success_url = parent.get_edit_url()
            else:
                success_url = "/"
        return HttpResponseRedirect(success_url)
    return TemplateResponse(request, 'delete_confirm.html')


def move_section(request, section_id, success_url=None):
    if request.method != "POST":
        return HttpResponse("only use POST for this")
    section = get_object_or_404(Section, id=section_id)
    section.save_version(request.user, "move section")

    form = MoveSectionForm(request.POST, instance=section)
    if form.is_valid():
        to_section = get_object_or_404(
            Section,
            id=form.cleaned_data['_ref_node_id'])
        position = form.cleaned_data['_position']
        section.move(to_section, position)
        parent = section.get_parent()
        if parent:
            section.clear_tree_cache()
        to_section.clear_tree_cache()
        if success_url is None:
            success_url = to_section.get_edit_url()
        return HttpResponseRedirect(success_url)
    return HttpResponse("could not move section")


def add_pageblock(request, section_id, success_url=None):
    section = get_object_or_404(Section, id=section_id)
    blocktype = request.POST.get('blocktype', '')
    section.save_version(user=request.user,
                         activity="add pageblock [%s]" % blocktype)
    # now we need to figure out which kind of pageblock to create
    for pb_class in section.available_pageblocks():
        if pb_class.display_name == blocktype:
            # a match
            block = pb_class.create(request)
            section.append_pageblock(
                label=request.POST.get('label', ''),
                css_extra=request.POST.get('css_extra', ''),
                content_object=block)
    if success_url is None:
        success_url = section.get_edit_url()
    return HttpResponseRedirect(success_url)


def add_child_section(request, section_id, success_url=None):
    section = get_object_or_404(Section, id=section_id)
    label = request.POST.get('label', 'unnamed') or 'unnamed'
    section.save_version(
        request.user,
        "add child section [%s]" % label)
    slug = slugify(request.POST.get('slug', label))[:50]
    section.append_child(label, slug)
    section.clear_tree_cache()
    if success_url is None:
        success_url = section.get_edit_url()
    return HttpResponseRedirect(success_url)


def create_tree_root(request):
    get_section_from_path("")  # creates a root if one doesn't exist
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def exporter(request):
    hierarchy_name = request.GET.get('hierarchy', 'main')
    h = get_object_or_404(Hierarchy, name=hierarchy_name)
    data = h.as_dict()
    resources = []
    protocol = "http"
    if request.is_secure():
        protocol = "https"
    url_base = protocol + "//" + request.get_host()
    for pb in PageBlock.objects.filter(section__hierarchy=h):
        block = pb.block()
        if hasattr(block, 'list_resources'):
            for r in block.list_resources():
                resources.append(url_base + r)
    data['resources'] = resources
    resp = HttpResponse(dumps(data))
    resp['Content-Type'] = 'application/json'
    return resp


def revert_to_version(request, version_id):
    v = get_object_or_404(Version, pk=version_id)
    if request.method == "POST":
        v.section.save_version(
            request.user,
            activity="reverting to previous version [%d]" % v.id)
        # clear all pageblocks on the section
        for pb in v.section.pageblock_set.all():
            pb.delete()
        # clear child sections (since they might get replaced)
        v.section.get_children().delete()
        # force the numchild to 0.
        # possible treebeard bug we are working around
        # basically, despite calling the treebeard queryset's .delete()
        # as recommended, child nodes get deleted, but the parent's
        # numchild never gets reset, so
        #   section.get_num_children() returns, say, 3
        # while
        #   section.get_children() returns []
        # this really seems like a bug in treebeard, possibly
        # transaction related

        v.section.numchild = 0
        v.section.save()
        v.section.from_dict(loads(v.data))
        v.section.clear_tree_cache()
        return HttpResponseRedirect(v.section.get_edit_url())
    else:
        return render(request, "revert_confirm.html", dict(version=v))
