from __future__ import unicode_literals

"""
allow you to pull a pagetree root directly into a template variable.

especially handy for getting navigation/menu stuff into eg, flatpage or
404 templates since you don't have to inject stuff into the views.


Example:

{% load getroot %}

{% getroot main as root %}
{% for section in root.get_children %}
<li>... top level sections ...</li>
{% endfor %}

"""
from django import template
from pagetree.helpers import get_hierarchy

register = template.Library()


class GetRootNode(template.Node):
    def __init__(self, hierarchy, var_name):
        self.hierarchy = hierarchy
        self.var_name = var_name

    def render(self, context):
        h = get_hierarchy(self.hierarchy)
        r = h.get_root()
        context[self.var_name] = r
        return ''


@register.tag('getroot')
def getroot(parser, token):
    hierarchy = token.split_contents()[1:][0]
    var_name = token.split_contents()[1:][2]
    return GetRootNode(hierarchy, var_name)
