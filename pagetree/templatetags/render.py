""" render templatetag 

let's us do {% render block %}

instead of {{block.render}}

and have block.render() get called with the existing
request context passed through

"""

from django import template

register = template.Library()

class RenderNode(template.Node):
    def __init__(self, block):
        self.block = block

    def render(self, context):
        b = context[self.block]
        r = context['request']
        context_dict = {}
        for d in context.dicts:
            context_dict.update(d)
        # can only take string keys
        for k in context_dict.keys():
            if type(k) != type(''):
                del context_dict[k]
        return b.render(**context_dict)

@register.tag('render')
def render(parser, token):
    block = token.split_contents()[1:][0]
    return RenderNode(block)
