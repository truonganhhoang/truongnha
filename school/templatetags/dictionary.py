# -*- coding: utf-8 -*-
from django import template

register = template.Library()

@register.filter(name='get_value')
def get_value(d, k):
    if d == None: return None
    if k == None: return None
    if not k in d: return None
    return d[k]

