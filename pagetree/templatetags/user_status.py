from __future__ import unicode_literals

from django import template
from django.utils.encoding import smart_str

register = template.Library()


class GetUserSectionStatus(template.Node):
    def __init__(self, user, section, var_name=None):
        self.user = template.Variable(user)
        self.section = template.Variable(section)
        self.var_name = var_name

    def render(self, context):
        u = self.user.resolve(context)
        s = self.section.resolve(context)
        upv = s.get_uservisit(u)
        if self.var_name:
            context[self.var_name] = upv
            return ''
        else:
            return upv


@register.tag('get_user_section_status')
def get_user_section_status(parser, token):
    user = token.split_contents()[1:][0]
    section = token.split_contents()[1:][1]
    var_name = None
    if len(token.split_contents()[1:]) > 2:
        # handle "as some_var"
        var_name = token.split_contents()[1:][3]
    return GetUserSectionStatus(user, section, var_name)


@register.simple_tag
def is_section_unlocked(section, user):
    if hasattr(section, 'unlocked'):
        is_unlocked = section.unlocked(user)
    else:
        is_unlocked = True

    # Convert to 1 or 0 to parse it easily in the template.
    return smart_str(int(is_unlocked))
