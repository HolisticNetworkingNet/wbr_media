import json
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.management.base import BaseCommand

from wbr_media.transfer.files import MediaFileExporter
from wbr_media.transfer.handler import WBRMediaHandler


class Command(BaseCommand):
    help = "Export WBR Media data and physical files into one bundle."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Path to write the WBR Media export bundle.",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])

        handler = WBRMediaHandler()
        data = handler.export_data(site=None, context=None)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            data_path = tmp_path / "data.json"
            data_path.write_text(
                json.dumps(data, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            media_dir = tmp_path / "media"
            media_result = MediaFileExporter(
                site=None,
                output_dir=media_dir,
            ).run()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with ZipFile(output_path, "w", ZIP_DEFLATED) as bundle:
                bundle.write(data_path, "data.json")
                bundle.write(media_result.zip_path, "media_export.zip")

        self.stdout.write(self.style.SUCCESS("WBR Media export complete."))
        self.stdout.write(f"Bundle: {output_path}")