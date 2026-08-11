from django import forms
from django.contrib import admin
from django.utils.html import format_html, mark_safe

from .models import MediaAsset


class MediaAssetUploadMixin:
    """Add a reusable MediaAsset upload panel to a ModelAdmin.

    Set ``media_field`` to the model field that relates to MediaAsset.
    """

    media_field = "image"
    change_form_template = "admin/wbr_media/mediaasset_upload/change_form.html"
    media_upload_fields = (
        "image_file",
        "image_title",
        "image_alt_text",
        "image_description",
    )

    def get_fieldsets(self, request, obj=None):
        content_fields = []
        if self.fieldsets is not None:
            for _name, options in self.fieldsets:
                content_fields.extend(options.get("fields", ()))
        else:
            content_fields.extend(
                field.name
                for field in self.model._meta.get_fields()
                if getattr(field, "editable", False)
                and not getattr(field, "auto_created", False)
                and field.name not in (self.exclude or ())
            )
        content_fields = [
            field
            for field in content_fields
            if field not in (self.media_field, "media_asset_preview")
            and field not in self.readonly_fields
        ]
        return (
            (None, {"fields": tuple(dict.fromkeys(content_fields))}),
            (
                "Media upload",
                {
                    "classes": ("image-panel",),
                    "fields": (
                        "image_file",
                        "media_asset_preview",
                        self.media_field,
                        "image_title",
                        "image_alt_text",
                        "image_description",
                    ),
                    "description": "Upload a file or select an existing media asset.",
                },
            ),
        )

    def get_form(self, request, obj=None, **kwargs):
        # Django validates fieldsets against the model before returning a form.
        # The upload fields are virtual form fields, so exclude them from that
        # first pass and add them to the generated form below.
        excluded = set(self.media_upload_fields) | {"media_asset_preview"}
        field_names = []
        for fieldset in self.get_fieldsets(request, obj):
            field_names.extend(
                name for name in fieldset[1].get("fields", ()) if name not in excluded
            )
        kwargs["fields"] = tuple(dict.fromkeys(field_names))
        form = super().get_form(request, obj, **kwargs)
        media = obj and getattr(obj, self.media_field, None)

        class MediaAssetUploadForm(form):
            image_file = forms.FileField(required=False, label="Upload file")
            image_title = forms.CharField(required=False, label="File title")
            image_alt_text = forms.CharField(required=False, label="Alt text")
            image_description = forms.CharField(
                required=False,
                label="Description",
                widget=forms.Textarea(attrs={"rows": 4}),
            )

            def __init__(self, *args, **form_kwargs):
                super().__init__(*args, **form_kwargs)
                if media:
                    self.fields["image_title"].initial = media.title
                    self.fields["image_alt_text"].initial = media.alt_text
                    self.fields["image_description"].initial = media.description

        return MediaAssetUploadForm

    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)
        uploaded = form.cleaned_data.get("image_file")
        if uploaded:
            asset = MediaAsset.objects.create(
                file=uploaded,
                title=form.cleaned_data.get("image_title", ""),
                alt_text=form.cleaned_data.get("image_alt_text", ""),
                description=form.cleaned_data.get("image_description", ""),
            )
            setattr(obj, self.media_field, asset)
        return obj

    @admin.display(description="Current representation")
    def media_asset_preview(self, obj):
        asset = getattr(obj, self.media_field, None) if obj else None
        if not asset or not asset.file:
            return mark_safe(
                '<div id="media-asset-preview" class="image-placeholder">No file</div>'
            )
        if asset.media_type == "image":
            return format_html(
                '<img id="media-asset-preview" src="{}" alt="{}">',
                asset.file.url,
                asset.alt_text or asset.title,
            )
        return mark_safe(
            '<div id="media-asset-preview" class="file-placeholder">File selected</div>'
        )
