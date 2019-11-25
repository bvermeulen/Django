from django import template

register = template.Library()

@register.simple_tag
def increment(counter):
    return counter + 1