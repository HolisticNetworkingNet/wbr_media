from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from wbr_media.models import MediaAsset


@receiver(post_delete, sender=MediaAsset)
def delete_file_on_delete(sender, instance, **kwargs):
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
        old.file.delete(save=False)