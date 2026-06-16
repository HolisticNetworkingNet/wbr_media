from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.conf import settings

from .views import media_demo

urlpatterns = [
    path('admin/', admin.site.urls),
    path("media-demo/", media_demo, name="media_demo"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
