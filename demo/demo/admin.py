from django.contrib import admin

from wbr_media.admin_mixins import MediaAssetUploadMixin

from .models import Page


@admin.register(Page)
class PageAdmin(MediaAssetUploadMixin, admin.ModelAdmin):
    media_fields = {"image": "Hero image", "thumbnail_media": "Thumbnail image"}
    list_display = ("title", "published", "image_status", "updated_at")
    list_filter = ("published",)
    search_fields = ("title", "slug", "body")
    prepopulated_fields = {"slug": ("title",)}

    @admin.display(description="Image")
    def image_status(self, obj):
        return "Uploaded" if obj.image_id else "None"
