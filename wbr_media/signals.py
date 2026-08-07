import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from wbr_media.models import MediaAsset
from wbr_media.services import generate_renditions, remove_renditions

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=MediaAsset)
def delete_file_on_delete(sender, instance, **kwargs):
    remove_renditions(instance.file.name if instance.file else "")
    if instance.file:
        instance.file.delete(save=False)


@receiver(pre_save, sender=MediaAsset)
def delete_old_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = MediaAsset.objects.get(pk=instance.pk)
    except MediaAsset.DoesNotExist:
        return
    if old.file and old.file != instance.file:
        remove_renditions(old.file.name)
        old.file.delete(save=False)


@receiver(post_save, sender=MediaAsset)
def generate_image_renditions(sender, instance, raw, **kwargs):
    if not raw:
        try:
            generate_renditions(instance)
        except Exception:
            # Thumbnail generation is derived work and must not make the
            # canonical upload fail. The original remains available for a
            # later retry through generate_thumbnails.
            logger.exception("Unable to generate thumbnails for asset %s", instance.pk)
