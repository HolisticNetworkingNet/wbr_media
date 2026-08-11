from collections.abc import Mapping

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html, mark_safe

from .models import MediaAsset


class MediaAssetUploadMixin:
    """Add one or more MediaAsset upload panels to a ModelAdmin.

    Configure one relationship with ``media_field = "image"`` or multiple
    relationships with ``media_fields = {"hero_media": "Hero image"}``.
    When both are configured, ``media_fields`` takes precedence.
    """

    media_field = "image"
    media_fields = None
    change_form_template = "admin/wbr_media/mediaasset_upload/change_form.html"

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        for field_name, _label in self._media_field_config():
            preview_name = self._media_names(field_name)["preview"]
            setattr(self, preview_name, self._preview_method(field_name))

    def _media_field_config(self):
        if self.media_fields is not None:
            if not isinstance(self.media_fields, Mapping) or not self.media_fields:
                raise ImproperlyConfigured(
                    "MediaAssetUploadMixin.media_fields must be a non-empty mapping."
                )
            config = tuple(self.media_fields.items())
        elif isinstance(self.media_field, str) and self.media_field:
            config = ((self.media_field, "Media upload"),)
        else:
            raise ImproperlyConfigured(
                "Configure media_field or a non-empty media_fields mapping."
            )

        for field_name, label in config:
            if not isinstance(field_name, str) or not field_name:
                raise ImproperlyConfigured(
                    "MediaAsset relationship names must be strings."
                )
            if not isinstance(label, str) or not label:
                raise ImproperlyConfigured(
                    "MediaAsset relationship labels must be strings."
                )
            try:
                model_field = self.model._meta.get_field(field_name)
            except Exception as exc:
                raise ImproperlyConfigured(
                    f"{self.model.__name__}.{field_name} is not a model field."
                ) from exc
            if (
                getattr(model_field, "remote_field", None) is None
                or model_field.remote_field.model is not MediaAsset
            ):
                raise ImproperlyConfigured(
                    f"{self.model.__name__}.{field_name} must relate to MediaAsset."
                )
        return config

    def _media_names(self, field_name):
        if self.media_fields is None:
            return {
                "file": "image_file",
                "title": "image_title",
                "alt": "image_alt_text",
                "description": "image_description",
                "preview": "media_asset_preview",
            }
        prefix = f"media__{field_name}__"
        return {
            "file": f"{prefix}file",
            "title": f"{prefix}title",
            "alt": f"{prefix}alt_text",
            "description": f"{prefix}description",
            "preview": f"{prefix}preview",
        }

    def get_readonly_fields(self, request, obj=None):
        base = super().get_readonly_fields(request, obj)
        return tuple(base) + tuple(
            self._media_names(field_name)["preview"]
            for field_name, _label in self._media_field_config()
        )

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = []
        if self.fieldsets is not None:
            for _name, options in self.fieldsets:
                base_fieldsets.append((_name, dict(options)))
        else:
            default_fields = tuple(
                field.name
                for field in self.model._meta.get_fields()
                if getattr(field, "editable", False)
                and not getattr(field, "auto_created", False)
                and field.name not in (self.exclude or ())
            )
            base_fieldsets.append((None, {"fields": default_fields}))
        media_fields = {field_name for field_name, _label in self._media_field_config()}
        preview_fields = {
            self._media_names(field_name)["preview"]
            for field_name, _label in self._media_field_config()
        }
        cleaned_fieldsets = []
        for name, options in base_fieldsets:
            fields = tuple(
                field
                for field in options.get("fields", ())
                if field not in media_fields
                and field not in preview_fields
                and field not in self.readonly_fields
            )
            if fields:
                options["fields"] = fields
                cleaned_fieldsets.append((name, options))
        panels = []
        for field_name, label in self._media_field_config():
            names = self._media_names(field_name)
            panels.append(
                (
                    label,
                    {
                        "classes": ("wbr-media-upload-panel",),
                        "fields": (
                            names["file"],
                            names["preview"],
                            field_name,
                            names["title"],
                            names["alt"],
                            names["description"],
                        ),
                        "description": "Upload a file or select an existing media asset.",
                    },
                )
            )
        return (*cleaned_fieldsets, *panels)

    def get_form(self, request, obj=None, **kwargs):
        config = self._media_field_config()
        virtual_fields = set()
        field_names = []
        for fieldset in self.get_fieldsets(request, obj):
            for name in fieldset[1].get("fields", ()):
                if name not in self.get_readonly_fields(request, obj):
                    field_names.append(name)
        for field_name, _label in config:
            virtual_fields.update(self._media_names(field_name).values())
        kwargs["fields"] = tuple(
            name for name in dict.fromkeys(field_names) if name not in virtual_fields
        )
        form = super().get_form(request, obj, **kwargs)
        media = {
            field_name: getattr(obj, field_name, None) if obj else None
            for field_name, _label in config
        }
        declarations = {}
        for field_name, _label in config:
            names = self._media_names(field_name)
            declarations[names["file"]] = forms.FileField(
                required=False, label="Upload file"
            )
            declarations[names["title"]] = forms.CharField(
                required=False, label="File title"
            )
            declarations[names["alt"]] = forms.CharField(
                required=False, label="Alt text"
            )
            declarations[names["description"]] = forms.CharField(
                required=False,
                label="Description",
                widget=forms.Textarea(attrs={"rows": 4}),
            )

        class MediaAssetUploadForm(form):
            def __init__(self, *args, **form_kwargs):
                super().__init__(*args, **form_kwargs)
                for field_name, _label in config:
                    asset = media[field_name]
                    names = self._media_names(field_name)
                    if asset:
                        self.fields[names["title"]].initial = asset.title
                        self.fields[names["alt"]].initial = asset.alt_text
                        self.fields[names["description"]].initial = asset.description

            def _media_names(self, field_name):
                return self._admin._media_names(field_name)

        MediaAssetUploadForm.base_fields.update(declarations)
        MediaAssetUploadForm._admin = self
        return MediaAssetUploadForm

    def save_form(self, request, form, change):
        original_assets = {
            field_name: getattr(form.instance, field_name, None)
            for field_name, _label in self._media_field_config()
        }
        for field_name, _label in self._media_field_config():
            if original_assets[field_name] is None:
                original_id = form.initial.get(field_name)
                if original_id:
                    original_assets[field_name] = MediaAsset.objects.filter(
                        pk=original_id
                    ).first()
        obj = super().save_form(request, form, change)
        for field_name, _label in self._media_field_config():
            names = self._media_names(field_name)
            asset = getattr(obj, field_name, None)
            uploaded = form.cleaned_data.get(names["file"])
            if uploaded:
                asset = MediaAsset.objects.create(
                    file=uploaded,
                    title=form.cleaned_data.get(names["title"], ""),
                    alt_text=form.cleaned_data.get(names["alt"], ""),
                    description=form.cleaned_data.get(names["description"], ""),
                )
                setattr(obj, field_name, asset)
            else:
                asset = original_assets[field_name] or asset
                if asset:
                    setattr(obj, field_name, asset)
            if not uploaded and asset:
                changed = False
                for attr, key in (
                    ("title", "title"),
                    ("alt_text", "alt"),
                    ("description", "description"),
                ):
                    value = form.cleaned_data.get(names[key], getattr(asset, attr))
                    if value != getattr(asset, attr):
                        setattr(asset, attr, value)
                        changed = True
                if changed:
                    asset.save(
                        update_fields=("title", "alt_text", "description", "updated_at")
                    )
        return obj

    def _preview_method(self, field_name):
        def preview(obj):
            asset = getattr(obj, field_name, None) if obj else None
            preview_id = self._media_names(field_name)["preview"]
            if not asset or not asset.file:
                return mark_safe(
                    f'<div id="{preview_id}" class="image-placeholder">No file</div>'
                )
            if asset.media_type == "image":
                return format_html(
                    '<img id="{}" src="{}" alt="{}">',
                    preview_id,
                    asset.file.url,
                    asset.alt_text or asset.title,
                )
            return mark_safe(
                f'<div id="{preview_id}" class="file-placeholder">File selected</div>'
            )

        preview.short_description = "Current representation"
        return preview
