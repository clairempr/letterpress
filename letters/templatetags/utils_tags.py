from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.simple_tag
def get_proper_elided_page_range(paginator, number, on_each_side=3, on_ends=2):
    """
    Paginator.get_elided_page_range() takes some arguments that can't be passed in when using it in a template,
    so do it with a template tag

    https://docs.djangoproject.com/en/3.2/ref/paginator/#django.core.paginator.Paginator.get_elided_page_range
    """
    p = Paginator(paginator.object_list, paginator.per_page)
    return p.get_elided_page_range(number=number,
                                   on_each_side=on_each_side,
                                   on_ends=on_ends)
