from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from .views import media_demo, page_detail

urlpatterns = [
    path("admin/", admin.site.urls),
    path("media-demo/", media_demo, name="media_demo"),
    path("pages/<slug:slug>/", page_detail, name="page_detail"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
