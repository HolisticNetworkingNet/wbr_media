from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import MediaAssetUploadForm
from .models import MediaAsset


@staff_member_required
def media_admin(request):
    form = MediaAssetUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        asset = form.save()
        return redirect(f"{reverse('media_admin')}?uploaded={asset.pk}")

    return render(
        request,
        "wbr_media/media_admin.html",
        {
            "form": form,
            "assets": MediaAsset.objects.order_by("-uploaded_at")[:24],
            "uploaded": request.GET.get("uploaded"),
        },
    )
