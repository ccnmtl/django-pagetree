from __future__ import unicode_literals

from django import template
register = template.Library()


@register.filter('hasrelated')
def hasrelated(obj):
    return len(obj._meta.get_all_related_objects()) > 0
