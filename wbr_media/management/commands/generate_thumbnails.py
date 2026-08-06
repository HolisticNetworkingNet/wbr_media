from django.core.management.base import BaseCommand, CommandError

from wbr_media.models import MediaAsset
from wbr_media.services import generate_renditions


class Command(BaseCommand):
    help = "Generate configured thumbnails for WBR Media image assets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--asset-id",
            dest="asset_ids",
            action="append",
            type=int,
            help="Only generate thumbnails for this asset ID; may be repeated.",
        )

    def handle(self, *args, **options):
        asset_ids = options["asset_ids"]
        assets = MediaAsset.objects.filter(media_type="image").order_by("pk")
        if asset_ids:
            assets = assets.filter(pk__in=asset_ids)

        processed = 0
        generated = 0
        failures = []

        for asset in assets:
            try:
                paths = generate_renditions(asset)
            except Exception as exc:  # pragma: no cover - command boundary
                failures.append(f"{asset.pk}: {exc}")
                continue

            processed += 1
            generated += len(paths)
            self.stdout.write(f"Asset {asset.pk}: generated {len(paths)} thumbnail(s)")

        self.stdout.write(
            self.style.SUCCESS(
                f"Thumbnail generation complete. Assets: {processed}; "
                f"thumbnails: {generated}."
            )
        )

        if failures:
            self.stdout.write(self.style.ERROR(f"Failures: {len(failures)}"))
            for failure in failures:
                self.stdout.write(f"- {failure}")
            raise CommandError("One or more assets could not be processed.")
