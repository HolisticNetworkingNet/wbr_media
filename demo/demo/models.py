from django.db import models
from django.urls import reverse

from wbr_media.models import MediaAsset


class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    image = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name="pages"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("page_detail", kwargs={"slug": self.slug})
