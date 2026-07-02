from pathlib import Path
from shutil import move, rmtree

from django.core.management.base import BaseCommand

from wbr_media.transfer.files import MediaFileExporter


class Command(BaseCommand):
    help = "Export WBR Media files and write a media manifest."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Directory to export media files to.",
        )

        parser.add_argument(
            "--clean",
            action="store_true",
            help="Remove the staging files after creating the zip.",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output"])
        clean = options["clean"]

        result = MediaFileExporter(
            site=None,
            output_dir=output_dir,
        ).run()

        if clean:
            final_zip_path = result.output_directory.parent / result.zip_path.name

            if final_zip_path.exists():
                final_zip_path.unlink()

            move(str(result.zip_path), str(final_zip_path))
            rmtree(result.output_directory)

            self.stdout.write(
                self.style.SUCCESS(f"Cleaned export directory: {result.output_directory}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Final zip: {final_zip_path}")
            )

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