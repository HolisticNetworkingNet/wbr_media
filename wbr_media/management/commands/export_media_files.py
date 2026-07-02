from pathlib import Path

from django.core.management.base import BaseCommand

from wbr_media.exporting.files import MediaFileExporter


class Command(BaseCommand):
    help = "Export WBR Media files and write a media manifest."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Directory where exported media files and manifest will be written.",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output"])

        result = MediaFileExporter(
            site=None,
            output_dir=output_dir,
        ).run()

        self.stdout.write(self.style.SUCCESS("Media export complete."))

        self.stdout.write(f"Output directory: {result.output_directory}")
        self.stdout.write(f"Files directory: {result.files_directory}")
        self.stdout.write(f"Manifest: {result.manifest_path}")
        self.stdout.write(f"Zip: {result.zip_path}")
        self.stdout.write(f"Assets exported: {len(result.assets)}")

        if result.validation_errors:
            self.stdout.write(self.style.ERROR("Validation: failed"))

            for error in result.validation_errors:
                self.stdout.write(f"- {error}")
        else:
            self.stdout.write(self.style.SUCCESS("Validation: passed"))