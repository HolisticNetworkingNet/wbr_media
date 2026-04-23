from django.shortcuts import render
from wbr_media.models import MediaAsset


def media_demo(request):
    assets = MediaAsset.objects.all().order_by("-uploaded_at")
    return render(request, "media_demo.html", {"assets": assets})