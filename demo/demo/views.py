from django.shortcuts import render

from wbr_media.models import MediaAsset

from .models import Page


def media_demo(request):
    assets = MediaAsset.objects.all().order_by("-uploaded_at")
    return render(request, "media_demo.html", {"assets": assets})


def page_detail(request, slug):
    page = Page.objects.get(slug=slug, published=True)
    return render(request, "page_detail.html", {"page": page})
