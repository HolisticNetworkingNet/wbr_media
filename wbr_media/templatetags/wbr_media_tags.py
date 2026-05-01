from django import template
from django.template.loader import select_template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_media(asset, size="full", display=None, class_name="", alt=""):
    """
    Render a MediaAsset using app-defined templates.

    Args:
        asset: MediaAsset instance
        size: named size/rendition (default: "full")
        display: rendering mode ("figure", "bare", "link")
        class_name: optional CSS class passthrough
    """

    if not asset or not asset.file:
        return ""

    # --- Default display behavior ---
    if display is None:
        display = "figure" if asset.media_type == "image" else "link"

    # --- Resolve media URL (future: renditions) ---
    media_url = asset.file.url

    # --- Template resolution order ---
    template_candidates = [
        f"wbr_media/renderers/{asset.media_type}/{display}.html",
        f"wbr_media/renderers/{display}.html",
        "wbr_media/renderers/generic.html",
    ]

    template_obj = select_template(template_candidates)

    context = {
        "asset": asset,
        "size": size,
        "display": display,
        "class_name": class_name,
        "media_url": media_url,
        "alt": alt,
    }

    return mark_safe(template_obj.render(context))