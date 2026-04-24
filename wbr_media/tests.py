import io
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from django.template import Context, Template

from wbr_media.models import ImageMetadata, MediaAsset


def build_png_bytes(size=(20, 10), color=(255, 0, 0, 255), image_format="PNG"):
    buffer = io.BytesIO()
    image = Image.new("RGBA", size, color)
    image.save(buffer, format=image_format)
    return buffer.getvalue()


class MediaAssetBaseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self._temp_media_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._temp_media_dir, ignore_errors=True))
        self.settings_override = override_settings(
            MEDIA_ROOT=self._temp_media_dir,
            WBR_MEDIA={"UPLOAD_TO": "test_uploads/%Y/%m"},
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)


class MediaAssetCrudTests(MediaAssetBaseTestCase):
    def test_create_image_persists_file_and_extracts_metadata(self):
        uploaded = SimpleUploadedFile(
            "sample.png",
            build_png_bytes(size=(64, 48)),
            content_type="image/png",
        )
        asset = MediaAsset.objects.create(title="Sample image", file=uploaded)

        self.assertTrue(Path(asset.file.path).exists())
        self.assertEqual(asset.file_name, "sample.png")
        self.assertEqual(asset.mime_type, "image/png")
        self.assertEqual(asset.media_type, "image")
        self.assertGreater(asset.file_size, 0)

        with asset.file.open("rb") as stored:
            with Image.open(io.BytesIO(stored.read())) as saved_image:
                self.assertEqual(saved_image.size, (64, 48))

        metadata = ImageMetadata.objects.get(media=asset)
        self.assertEqual(metadata.width, 64)
        self.assertEqual(metadata.height, 48)
        self.assertEqual(metadata.format, "PNG")
        self.assertTrue(metadata.has_alpha)

    def test_create_non_image_sets_document_type_and_no_image_metadata(self):
        uploaded = SimpleUploadedFile(
            "notes.txt",
            b"plain text body",
            content_type="text/plain",
        )
        asset = MediaAsset.objects.create(file=uploaded)

        self.assertTrue(Path(asset.file.path).exists())
        self.assertEqual(asset.file_name, "notes.txt")
        self.assertEqual(asset.mime_type, "text/plain")
        self.assertEqual(asset.media_type, "document")
        self.assertFalse(ImageMetadata.objects.filter(media=asset).exists())

    def test_update_replaces_file_and_deletes_old_file_from_storage(self):
        original = MediaAsset.objects.create(
            file=SimpleUploadedFile(
                "first.png",
                build_png_bytes(size=(10, 10)),
                content_type="image/png",
            )
        )
        old_path = original.file.path
        self.assertTrue(Path(old_path).exists())
        self.assertTrue(ImageMetadata.objects.filter(media=original).exists())

        replacement = SimpleUploadedFile(
            "second.txt",
            b"replacement payload",
            content_type="text/plain",
        )
        original.file = replacement
        original.save()
        original.refresh_from_db()

        self.assertFalse(Path(old_path).exists())
        self.assertTrue(Path(original.file.path).exists())
        self.assertEqual(original.file_name, "second.txt")
        self.assertEqual(original.mime_type, "text/plain")
        self.assertEqual(original.media_type, "document")
        self.assertFalse(ImageMetadata.objects.filter(media=original).exists())

    def test_delete_removes_file_from_local_storage(self):
        asset = MediaAsset.objects.create(
            file=SimpleUploadedFile(
                "delete-me.png",
                build_png_bytes(size=(8, 8)),
                content_type="image/png",
            )
        )
        file_path = asset.file.path
        self.assertTrue(Path(file_path).exists())

        asset.delete()

        self.assertFalse(Path(file_path).exists())
        self.assertEqual(MediaAsset.objects.count(), 0)
        self.assertEqual(ImageMetadata.objects.count(), 0)
