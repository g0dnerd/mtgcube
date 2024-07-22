from django import template
from django.templatetags.static import static
import time


register = template.Library()


@register.simple_tag
def versioned_static(path):
    file_url = static(path)
    now = int(time.time())
    return f"{file_url}?v={now}"
