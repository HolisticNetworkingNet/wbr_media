from django.core.management.base import BaseCommand

from wbr_media.transfer.files import MediaFileImporter


class Command(BaseCommand):
    help = "Restore WBR Media physical files from a media export zip."

    def add_arguments(self, parser):
        parser.add_argument("zip_path")

    def handle(self, *args, **options):
        result = MediaFileImporter(options["zip_path"]).restore()

        if result.validation_errors:
            self.stdout.write(self.style.ERROR("Media restore failed validation."))

            for error in result.validation_errors:
                self.stdout.write(f"- {error}")

            return

        self.stdout.write(self.style.SUCCESS("Media restore complete."))
        self.stdout.write(f"Zip: {result.zip_path}")
        self.stdout.write(f"Restored files: {len(result.restored)}")
        self.stdout.write(f"Skipped files: {len(result.skipped)}")