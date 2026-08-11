from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from wbr_media.models import MediaAsset

from .admin import PageAdmin
from .models import Page


class PageAdminUploadTests(TestCase):
    def setUp(self):
        self.admin = PageAdmin(Page, AdminSite())
        self.request = SimpleNamespace()

    def test_mixin_builds_complete_upload_panel(self):
        fieldsets = self.admin.get_fieldsets(self.request)
        self.assertEqual(
            fieldsets[1][1]["fields"],
            (
                "image_file",
                "media_asset_preview",
                "image",
                "image_title",
                "image_alt_text",
                "image_description",
            ),
        )

    def test_mixin_prefills_existing_asset_metadata(self):
        asset = MediaAsset.objects.create(
            title="Existing title",
            alt_text="Existing alt",
            description="Existing description",
            file=SimpleUploadedFile(
                "existing.txt", b"content", content_type="text/plain"
            ),
        )
        page = Page.objects.create(title="Existing page", slug="existing", image=asset)
        form = self.admin.get_form(self.request, page)(instance=page)
        self.assertEqual(form.fields["image_title"].initial, "Existing title")
        self.assertEqual(form.fields["image_alt_text"].initial, "Existing alt")
        self.assertEqual(
            form.fields["image_description"].initial, "Existing description"
        )

    def test_upload_attaches_new_asset_and_keeps_old_one(self):
        old_asset = MediaAsset.objects.create(
            file=SimpleUploadedFile("old.txt", b"old", content_type="text/plain")
        )
        page = Page.objects.create(
            title="Replaceable", slug="replaceable", image=old_asset
        )
        form = self.admin.get_form(self.request, page)(
            {
                "title": page.title,
                "slug": page.slug,
                "body": "",
                "published": "",
                "image": old_asset.pk,
                "image_title": "New title",
                "image_alt_text": "New alt",
                "image_description": "New description",
            },
            {
                "image_file": SimpleUploadedFile(
                    "new.bin", b"new", content_type="application/octet-stream"
                )
            },
            instance=page,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = self.admin.save_form(self.request, form, change=True)
        updated.save()
        self.assertEqual(MediaAsset.objects.count(), 2)
        self.assertEqual(updated.image.file_name, "new.bin")
        self.assertTrue(MediaAsset.objects.filter(pk=old_asset.pk).exists())
