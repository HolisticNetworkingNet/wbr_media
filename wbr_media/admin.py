from django.contrib import admin
from .models import MediaAsset
from django.utils.html import format_html


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "thumbnail", "title", "uploaded_at")

    def thumbnail(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="height: 50px; width: auto;" />',
                obj.file.url
            )
        return "-"