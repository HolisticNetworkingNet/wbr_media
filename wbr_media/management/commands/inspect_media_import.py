from django.core.management.base import BaseCommand

from wbr_media.transfer.files import MediaFileImporter


class Command(BaseCommand):
    help = "Inspect a WBR Media export zip without restoring files."

    def add_arguments(self, parser):
        parser.add_argument(
            "zip_path",
            help="Path to the media export zip.",
        )

    def handle(self, *args, **options):
        plan = MediaFileImporter(options["zip_path"]).inspect()

        self.stdout.write(f"Zip: {plan.zip_path}")
        self.stdout.write(f"Manifest assets: {len(plan.assets)}")
        self.stdout.write(f"Archive files: {len(plan.archive_paths)}")

        if plan.validation_errors:
            self.stdout.write(self.style.ERROR("Import inspection: failed"))

            for error in plan.validation_errors:
                self.stdout.write(f"- {error}")

            return

        self.stdout.write(self.style.SUCCESS("Import inspection: passed"))