from django import forms
from django.contrib import admin
from django.utils.html import format_html, mark_safe

from wbr_media.models import MediaAsset

from .models import Page


class PageAdminForm(forms.ModelForm):
    image_file = forms.FileField(required=False, label="Upload image")
    image_title = forms.CharField(required=False, label="Image title")
    image_alt_text = forms.CharField(required=False, label="Alt text")
    image_description = forms.CharField(
        required=False, label="Description", widget=forms.Textarea(attrs={"rows": 4})
    )

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
        (
            "Page image",
            {
                "classes": ("image-panel",),
                "fields": (
                    "image_file",
                    "image_preview",
                    "image",
                    "image_title",
                    "image_alt_text",
                    "image_description",
                ),
                "description": "Upload a new image or select an existing media asset.",
            },
        ),
    )

    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)
        uploaded = form.cleaned_data.get("image_file")
        if uploaded:
            obj.image = MediaAsset.objects.create(
                file=uploaded,
                title=form.cleaned_data.get("image_title", ""),
                alt_text=form.cleaned_data.get("image_alt_text", ""),
                description=form.cleaned_data.get("image_description", ""),
            )
        return obj

    readonly_fields = ("image_preview",)

    @admin.display(description="Current representation")
    def image_preview(self, obj):
        if not obj or not obj.image_id or not obj.image.file:
            return mark_safe('<div class="image-placeholder">No image</div>')
        if obj.image.media_type == "image":
            return format_html(
                '<img src="{}" alt="{}">', obj.image.file.url, obj.image.alt_text or obj.title
            )
        return format_html('<a href="{}">Open uploaded file</a>', obj.image.file.url)

    @admin.display(description="Image")
    def image_status(self, obj):
        return "Uploaded" if obj.image_id else "None"
