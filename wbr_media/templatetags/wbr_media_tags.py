from django import template
from django.template.loader import select_template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_media(asset):
    if not asset or not asset.file:
        return ""

    template_obj = select_template([
        f"wbr_media/renderers/{asset.media_type}.html",
        "wbr_media/renderers/generic.html",
    ])
    return mark_safe(template_obj.render({"asset": asset}))