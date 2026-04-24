from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import ImageMetadata, MediaAsset


class ImageMetadataInline(admin.StackedInline):
    model = ImageMetadata
    can_delete = False
    extra = 0

    readonly_fields = (
        "width",
        "height",
        "format",
        "color_mode",
        "has_alpha",
        "dpi_x",
        "dpi_y",
    )

    fields = readonly_fields

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "linked_title",
        "media_type",
        "file_size_display",
        "mime_type",
        "uploaded_at",
    )

    list_filter = (
        "media_type",
        "mime_type",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "file_name",
        "description",
        "mime_type",
    )

    ordering = ("-uploaded_at",)

    list_per_page = 25

    inlines = (ImageMetadataInline,)

    readonly_fields = (
        "admin_preview",
        "file_name",
        "file_size",
        "mime_type",
        "media_type",
        "uploaded_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Preview",
            {
                "fields": ("admin_preview",),
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "file",
                    "title",
                    "alt_text",
                    "description",
                ),
            },
        ),
        (
            "File metadata",
            {
                "fields": (
                    "file_name",
                    "file_size",
                    "mime_type",
                    "media_type",
                ),
            },
        ),
        (
            "System",
            {
                "classes": ("collapse",),
                "fields": (
                    "uploaded_at",
                    "updated_at",
                ),
            },
        ),
    )

    def file_size_display(self, obj):
        if obj.file_size is None:
            return "-"

        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024

        return f"{size:.1f} TB"

    file_size_display.short_description = "Size"

    def preview(self, obj):
        if not obj.file:
            return "-"

        if obj.media_type == "image":
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="height: 70px; width: auto; border-radius: 6px;" />'
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
            '<a href="{}" target="_blank">'
            '<img src="{}" style="max-width: 600px; max-height: 400px; width: auto; height: auto; border: 1px solid #ddd; border-radius: 6px;" />'
            "</a>",
            obj.file.url,
            obj.file.url,
        )

    admin_preview.short_description = "Preview"