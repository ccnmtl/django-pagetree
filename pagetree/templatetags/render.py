from __future__ import unicode_literals

""" render templatetag

let's us do {% render block %}

instead of {{block.render}}

and have block.render() get called with the existing
request context passed through

"""

from six import string_types
from django import template

register = template.Library()


class BaseNode(template.Node):
    def __init__(self, block):
        self.block = block

    def prepare_context_data(self, context):
        b = context[self.block]
        context_dict = {}
        for d in context.dicts:
            context_dict.update(d)
        # can only take string keys
        for k in context_dict.keys():
            if not isinstance(k, string_types):
                del context_dict[k]
        return b, context_dict


class RenderNode(BaseNode):
    def render(self, context):
        b, context_dict = super(RenderNode, self).prepare_context_data(context)
        return b.render(**context_dict)


@register.tag('render')
def render(parser, token):
    block = token.split_contents()[1:][0]
    return RenderNode(block)


class RenderJSNode(BaseNode):
    def render(self, context):
        b, context_dict = super(
            RenderJSNode, self).prepare_context_data(context)
        return b.render_js(**context_dict)


@register.tag('renderjs')
def renderjs(parser, token):
    block = token.split_contents()[1:][0]
    return RenderJSNode(block)


class RenderCSSNode(BaseNode):
    def render(self, context):
        b, context_dict = super(
            RenderCSSNode, self).prepare_context_data(context)
        return b.render_css(**context_dict)


@register.tag('rendercss')
def rendercss(parser, token):
    block = token.split_contents()[1:][0]
    return RenderCSSNode(block)


class RenderSummaryNode(BaseNode):
    def render(self, context):
        b, context_dict = super(
            RenderSummaryNode, self).prepare_context_data(context)
        return b.render_summary(**context_dict)


@register.tag('rendersummary')
def rendersummary(parser, token):
    block = token.split_contents()[1:][0]
    return RenderSummaryNode(block)
