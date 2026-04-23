from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("preview", "linked_title", "media_type", "uploaded_at")
    readonly_fields = (
        "admin_preview",
        "file_name",
        "file_size",
        "mime_type",
        "media_type",
        "uploaded_at",
        "updated_at",
    )

    fields = (
        "admin_preview",
        "file",
        "title",
        "alt_text",
        "description",
        "file_name",
        "file_size",
        "mime_type",
        "media_type",
        "uploaded_at",
        "updated_at",
    )

    def preview(self, obj):
        if not obj.file:
            return "-"

        if obj.media_type == "image":
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="height: 50px; width: auto;" />'
                "</a>",
                obj.file.url,
                obj.file.url,
            )

        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.file.url,
            obj.media_type or "file",
        )

    preview.short_description = "Preview"

    def linked_title(self, obj):
        url = reverse("admin:wbr_media_mediaasset_change", args=[obj.pk])
        label = obj.title or obj.file_name or obj.file.name
        return format_html('<a href="{}">{}</a>', url, label)

    linked_title.short_description = "Title"

    def admin_preview(self, obj):
        if not obj or not obj.pk or not obj.file:
            return "Preview available after save."

        if obj.media_type != "image":
            return "No image preview for this media type."

        return format_html(
            '<a href="{0}" target="_blank">'
            '<img src="{0}" style="max-width: 600px; max-height: 400px; width: auto; height: auto; border: 1px solid #ddd; border-radius: 6px;" />'
            "</a>",
            obj.file.url,
        )

    admin_preview.short_description = "Preview"