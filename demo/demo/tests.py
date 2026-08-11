from types import SimpleNamespace

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from wbr_media.admin_mixins import MediaAssetUploadMixin
from wbr_media.models import MediaAsset

from .admin import PageAdmin
from .models import Page


class SinglePageAdmin(MediaAssetUploadMixin, admin.ModelAdmin):
    media_field = "image"
    media_fields = None


class InvalidPageAdmin(MediaAssetUploadMixin, admin.ModelAdmin):
    media_field = None
    media_fields = {}


class GroupedPageAdmin(PageAdmin):
    fieldsets = (
        ("Content", {"fields": ("title", "slug")}),
        ("Publishing", {"fields": ("body", "published", "image")}),
    )


class PageAdminUploadTests(TestCase):
    def setUp(self):
        self.admin = PageAdmin(Page, AdminSite())
        self.single_admin = SinglePageAdmin(Page, AdminSite())
        self.request = SimpleNamespace()

    def test_mixin_builds_complete_upload_panel(self):
        fieldsets = self.admin.get_fieldsets(self.request)
        self.assertEqual(len(fieldsets), 3)
        self.assertEqual(fieldsets[1][0], "Hero image")
        self.assertEqual(fieldsets[2][0], "Thumbnail image")
        self.assertIn("media__image__file", fieldsets[1][1]["fields"])
        self.assertIn("media__thumbnail_media__file", fieldsets[2][1]["fields"])
        single_fields = self.single_admin.get_fieldsets(self.request)[1][1]["fields"]
        self.assertIn("image_file", single_fields)
        self.assertNotIn("media__image__file", single_fields)
        grouped = GroupedPageAdmin(Page, AdminSite()).get_fieldsets(self.request)
        self.assertEqual(
            [fieldset[0] for fieldset in grouped],
            ["Content", "Publishing", "Hero image", "Thumbnail image"],
        )
        self.assertEqual(grouped[0][1]["fields"], ("title", "slug"))
        self.assertEqual(grouped[1][1]["fields"], ("body", "published"))

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
        self.assertEqual(form.fields["media__image__title"].initial, "Existing title")
        self.assertEqual(form.fields["media__image__alt_text"].initial, "Existing alt")
        self.assertEqual(
            form.fields["media__image__description"].initial, "Existing description"
        )

    def test_upload_attaches_new_asset_and_keeps_old_one(self):
        old_asset = MediaAsset.objects.create(
            file=SimpleUploadedFile("old.txt", b"old", content_type="text/plain")
        )
        page = Page.objects.create(
            title="Replaceable", slug="replaceable", image=old_asset
        )
        form = self.single_admin.get_form(self.request, page)(
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
        updated = self.single_admin.save_form(self.request, form, change=True)
        updated.save()
        self.assertEqual(MediaAsset.objects.count(), 2)
        self.assertEqual(updated.image.file_name, "new.bin")
        self.assertTrue(MediaAsset.objects.filter(pk=old_asset.pk).exists())

    def test_multiple_uploads_are_assigned_independently(self):
        page = Page.objects.create(title="Portfolio", slug="portfolio")
        form = self.admin.get_form(self.request, page)(
            {"title": page.title, "slug": page.slug, "body": "", "published": ""},
            {
                "media__image__file": SimpleUploadedFile("hero.jpg", b"hero"),
                "media__image__title": "Hero",
                "media__thumbnail_media__file": SimpleUploadedFile(
                    "thumb.mp3", b"thumb"
                ),
                "media__thumbnail_media__title": "Thumb",
            },
            instance=page,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = self.admin.save_form(self.request, form, change=False)
        updated.save()
        self.assertEqual(updated.image.file_name, "hero.jpg")
        self.assertEqual(updated.thumbnail_media.file_name, "thumb.mp3")
        self.assertEqual(MediaAsset.objects.count(), 2)

    def test_blank_upload_preserves_relationship_and_metadata_update_is_supported(self):
        hero = MediaAsset.objects.create(
            title="Old hero",
            alt_text="Old alt",
            description="Old description",
            file=SimpleUploadedFile("hero.jpg", b"hero"),
        )
        thumb = MediaAsset.objects.create(
            title="Thumb",
            file=SimpleUploadedFile("thumb.mp3", b"thumb"),
        )
        page = Page.objects.create(
            title="Portfolio", slug="metadata", image=hero, thumbnail_media=thumb
        )
        form = self.admin.get_form(self.request, page)(
            {
                "title": page.title,
                "slug": page.slug,
                "body": "",
                "published": "",
                "media__image__title": "Updated hero",
                "media__image__alt_text": "Updated alt",
                "media__image__description": "Updated description",
                "media__thumbnail_media__title": "Thumb",
            },
            {},
            instance=page,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = self.admin.save_form(self.request, form, change=True)
        updated.save()
        hero.refresh_from_db()
        self.assertEqual(updated.image_id, hero.pk)
        self.assertEqual(updated.thumbnail_media_id, thumb.pk)
        self.assertEqual(hero.title, "Updated hero")
        self.assertEqual(hero.file_name, "hero.jpg")

    def test_non_image_media_is_supported(self):
        page = Page.objects.create(title="Audio", slug="audio")
        form = self.admin.get_form(self.request, page)(
            {
                "title": page.title,
                "slug": page.slug,
                "body": "",
                "published": "",
                "media__thumbnail_media__title": "Audio upload",
            },
            {"media__thumbnail_media__file": SimpleUploadedFile("clip.mp3", b"audio")},
            instance=page,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = self.admin.save_form(self.request, form, change=False)
        updated.save()
        self.assertEqual(updated.thumbnail_media.media_type, "audio")

    def test_missing_media_configuration_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            InvalidPageAdmin(Page, AdminSite()).get_fieldsets(self.request)
