from mimetypes import guess_type

from django.conf import settings
from django.db import models
from django.utils import timezone
from PIL import Image


def media_upload_path(instance, filename):
    config = getattr(settings, "WBR_MEDIA", {})
    base = config.get("UPLOAD_TO", "media/content/%Y/%m/")
    path = timezone.now().strftime(base)
    return f"{path}/{filename}"


def classify_media_type(mime_type):
    if not mime_type:
        return ""

    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type in {"application/pdf", "application/msword"}:
        return "document"
    if mime_type.startswith("text/"):
        return "document"

    return "other"


class MediaAsset(models.Model):
    file = models.FileField(upload_to=media_upload_path)

    # Human layer
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # File metadata (universal)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    # Classification (lightweight, not enforced)
    media_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="image, audio, video, document, etc.",
    )

    # System fields
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or self.file_name or self.file.name

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split("/")[-1]
            self.file_size = self.file.size

            mime_type, _ = guess_type(self.file.name)
            self.mime_type = mime_type or ""
            self.media_type = classify_media_type(self.mime_type)

        super().save(*args, **kwargs)

        if self.media_type == "image" and self.file:
            self._update_image_metadata()
        else:
            ImageMetadata.objects.filter(media=self).delete()

    def _update_image_metadata(self):
        try:
            self.file.open("rb")
            with Image.open(self.file) as img:
                width, height = img.size
                image_format = img.format or ""
                color_mode = img.mode or ""
                has_alpha = "A" in img.getbands()

                dpi = img.info.get("dpi")
                dpi_x = int(dpi[0]) if dpi and len(dpi) > 0 else None
                dpi_y = int(dpi[1]) if dpi and len(dpi) > 1 else None

            ImageMetadata.objects.update_or_create(
                media=self,
                defaults={
                    "width": width,
                    "height": height,
                    "format": image_format,
                    "color_mode": color_mode,
                    "has_alpha": has_alpha,
                    "dpi_x": dpi_x,
                    "dpi_y": dpi_y,
                },
            )
        except Exception:
            # Leave image metadata absent if Pillow cannot read the file.
            ImageMetadata.objects.filter(media=self).delete()
        finally:
            self.file.close()


class ImageMetadata(models.Model):
    media = models.OneToOneField(
        MediaAsset,
        on_delete=models.CASCADE,
        related_name="image_metadata",
    )

    width = models.IntegerField()
    height = models.IntegerField()
    format = models.CharField(max_length=50, blank=True)
    color_mode = models.CharField(max_length=50, blank=True)

    has_alpha = models.BooleanField(default=False)
    dpi_x = models.IntegerField(null=True, blank=True)
    dpi_y = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Image metadata for {self.media}"