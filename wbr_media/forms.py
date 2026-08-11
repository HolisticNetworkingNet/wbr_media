from django import forms

from .models import MediaAsset


class MediaAssetUploadForm(forms.ModelForm):
    class Meta:
        model = MediaAsset
        fields = ("file", "title", "alt_text", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
