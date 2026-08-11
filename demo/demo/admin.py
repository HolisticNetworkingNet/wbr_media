from django import forms
from django.contrib import admin

from wbr_media.models import MediaAsset

from .models import Page


class PageAdminForm(forms.ModelForm):
    image_file = forms.FileField(required=False, label="Upload image")

    class Meta:
        model = Page
        fields = ("title", "slug", "body", "published", "image")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    form = PageAdminForm
    list_display = ("title", "published", "image_status", "updated_at")
    list_filter = ("published",)
    search_fields = ("title", "slug", "body")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "body", "published")}),
        ("Page image", {"fields": ("image_file", "image"), "description": "Upload a new image or select an existing media asset."}),
    )

    def save_model(self, request, obj, form, change):
        uploaded = form.cleaned_data.get("image_file")
        if uploaded:
            obj.image = MediaAsset.objects.create(
                file=uploaded,
                title=form.cleaned_data.get("title", ""),
                alt_text=form.cleaned_data.get("title", ""),
            )
        super().save_model(request, obj, form, change)

    @admin.display(description="Image")
    def image_status(self, obj):
        return "Uploaded" if obj.image_id else "None"
