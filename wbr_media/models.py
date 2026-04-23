from django.db import models
from django.conf import settings
from datetime import datetime

def media_upload_path(instance, filename):
    base = settings.WBR_MEDIA.get("UPLOAD_TO", "media/content/%Y/%m/")
    now = datetime.now()
    path = now.strftime(base)
    return f"{path}/{filename}"

class MediaAsset(models.Model):
    file = models.ImageField(upload_to=media_upload_path)
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Useful metadata (we’ll populate later)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title or self.file.name