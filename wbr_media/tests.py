import io
import shutil
import tempfile
from pathlib import Path

from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from django.template import Context, Template

from wbr_media.admin import MediaAssetAdmin
from wbr_media.models import ImageMetadata, MediaAsset
from wbr_media.models import classify_media_type, media_upload_path


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

    def test_invalid_image_payload_does_not_persist_image_metadata(self):
        uploaded = SimpleUploadedFile(
            "broken.png",
            b"not a real image",
            content_type="image/png",
        )
        asset = MediaAsset.objects.create(file=uploaded)

        self.assertEqual(asset.media_type, "image")
        self.assertFalse(ImageMetadata.objects.filter(media=asset).exists())


class MediaHelpersTests(TestCase):
    def test_classify_media_type_handles_supported_groups(self):
        self.assertEqual(classify_media_type("image/png"), "image")
        self.assertEqual(classify_media_type("audio/mpeg"), "audio")
        self.assertEqual(classify_media_type("video/mp4"), "video")
        self.assertEqual(classify_media_type("application/pdf"), "document")
        self.assertEqual(classify_media_type("application/msword"), "document")
        self.assertEqual(classify_media_type("text/plain"), "document")
        self.assertEqual(classify_media_type("application/zip"), "other")
        self.assertEqual(classify_media_type(""), "")
        self.assertEqual(classify_media_type(None), "")

    @override_settings(WBR_MEDIA={"UPLOAD_TO": "assets/originals/%Y/%m"})
    def test_media_upload_path_uses_configured_pattern(self):
        path = media_upload_path(instance=None, filename="example.png")
        self.assertTrue(path.endswith("/example.png"))
        self.assertIn("assets/originals/", path)


class RenderMediaTemplateTagTests(MediaAssetBaseTestCase):
    def test_render_media_returns_empty_for_missing_asset_or_file(self):
        no_asset = Template("{% load wbr_media_tags %}{% render_media asset %}").render(
            Context({"asset": None})
        )
        no_file = Template("{% load wbr_media_tags %}{% render_media asset %}").render(
            Context({"asset": MediaAsset(title='No file')})
        )

        self.assertEqual(no_asset, "")
        self.assertEqual(no_file, "")

    def test_render_media_defaults_to_figure_for_images(self):
        asset = MediaAsset.objects.create(
            title="Sunset",
            description="Golden hour",
            file=SimpleUploadedFile(
                "sunset.png",
                build_png_bytes(size=(40, 20)),
                content_type="image/png",
            ),
        )
        rendered = Template("{% load wbr_media_tags %}{% render_media asset %}").render(
            Context({"asset": asset})
        )

        self.assertIn("<figure", rendered)
        self.assertIn("figcaption", rendered)
        self.assertIn("Golden hour", rendered)

    def test_render_media_defaults_to_link_for_documents(self):
        asset = MediaAsset.objects.create(
            title="Guide",
            file=SimpleUploadedFile(
                "guide.txt",
                b"hello",
                content_type="text/plain",
            ),
        )
        rendered = Template("{% load wbr_media_tags %}{% render_media asset %}").render(
            Context({"asset": asset})
        )

        self.assertIn("<a", rendered)
        self.assertIn("Guide", rendered)
        self.assertNotIn("<figure", rendered)

    def test_render_media_bare_image_uses_alt_and_class_name(self):
        asset = MediaAsset.objects.create(
            alt_text="Stored alt",
            file=SimpleUploadedFile(
                "plain.png",
                build_png_bytes(size=(30, 30)),
                content_type="image/png",
            ),
        )
        rendered = Template(
            "{% load wbr_media_tags %}{% render_media asset display='bare' class_name='hero' alt='Explicit alt' %}"
        ).render(Context({"asset": asset}))

        self.assertIn('<img', rendered)
        self.assertIn('class="hero"', rendered)
        self.assertIn('alt="Explicit alt"', rendered)

    def test_render_media_falls_back_to_generic_template(self):
        asset = MediaAsset.objects.create(
            title="Archive",
            file=SimpleUploadedFile(
                "archive.bin",
                b"\x00\x01\x02",
                content_type="application/octet-stream",
            ),
        )
        rendered = Template(
            "{% load wbr_media_tags %}{% render_media asset display='figure' %}"
        ).render(Context({"asset": asset}))

        self.assertIn("wbr-media--generic", rendered)
        self.assertIn("Archive", rendered)


class MediaAssetAdminTests(MediaAssetBaseTestCase):
    def setUp(self):
        super().setUp()
        self.admin = MediaAssetAdmin(MediaAsset, AdminSite())

    def test_file_size_display_formats_sizes(self):
        small = MediaAsset(file_size=512)
        kb = MediaAsset(file_size=2048)
        mb = MediaAsset(file_size=3 * 1024 * 1024)
        empty = MediaAsset(file_size=None)

        self.assertEqual(self.admin.file_size_display(empty), "-")
        self.assertEqual(self.admin.file_size_display(small), "512 B")
        self.assertEqual(self.admin.file_size_display(kb), "2.0 KB")
        self.assertEqual(self.admin.file_size_display(mb), "3.0 MB")

    def test_admin_preview_messages_for_unsaved_and_non_image(self):
        unsaved = MediaAsset(title="Unsaved")
        self.assertEqual(
            self.admin.admin_preview(unsaved),
            "Preview available after save.",
        )

        doc_asset = MediaAsset.objects.create(
            file=SimpleUploadedFile(
                "doc.txt",
                b"text",
                content_type="text/plain",
            )
        )
        self.assertEqual(
            self.admin.admin_preview(doc_asset),
            "No image preview for this media type.",
        )

    def test_linked_title_points_to_change_page(self):
        asset = MediaAsset.objects.create(
            title="Linked",
            file=SimpleUploadedFile(
                "linked.txt",
                b"content",
                content_type="text/plain",
            ),
        )
        html = self.admin.linked_title(asset)

        self.assertIn("Linked", html)
        self.assertIn(f"/admin/wbr_media/mediaasset/{asset.pk}/change/", html)


class DemoViewTests(MediaAssetBaseTestCase):
    def test_media_demo_view_renders_empty_state(self):
        response = self.client.get(reverse("media_demo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No media found.")

    def test_media_demo_view_renders_asset_cards(self):
        MediaAsset.objects.create(
            title="Demo image",
            file=SimpleUploadedFile(
                "demo.png",
                build_png_bytes(size=(20, 20)),
                content_type="image/png",
            ),
        )

        response = self.client.get(reverse("media_demo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo image")
        self.assertContains(response, "image")
