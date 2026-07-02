import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from django.core.management.base import BaseCommand, CommandError

from wbr_media.transfer.files import MediaFileImporter
from wbr_media.transfer.handler import WBRMediaHandler


class Command(BaseCommand):
    help = "Restore WBR Media data and physical files from one bundle."

    def add_arguments(self, parser):
        parser.add_argument(
            "bundle_path",
            help="Path to the WBR Media export bundle.",
        )

    def handle(self, *args, **options):
        bundle_path = Path(options["bundle_path"])

        if not bundle_path.exists():
            raise CommandError(f"Bundle does not exist: {bundle_path}")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            with ZipFile(bundle_path, "r") as bundle:
                names = set(bundle.namelist())

                if "data.json" not in names:
                    raise CommandError("Bundle missing data.json")

                if "media_export.zip" not in names:
                    raise CommandError("Bundle missing media_export.zip")

                bundle.extract("data.json", tmp_path)
                bundle.extract("media_export.zip", tmp_path)

            data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
            media_zip = tmp_path / "media_export.zip"

            restore_result = MediaFileImporter(media_zip).restore()

            if restore_result.validation_errors:
                for error in restore_result.validation_errors:
                    self.stderr.write(f"- {error}")

                raise CommandError("Media file restore failed validation.")

            context = SimpleNamespace(actions=[])
            handler = WBRMediaHandler()

            handler.validate(data, context)
            imported = handler.import_data(data, context)

        self.stdout.write(self.style.SUCCESS("WBR Media restore complete."))
        self.stdout.write(f"Bundle: {bundle_path}")
        self.stdout.write(f"Files restored: {len(restore_result.restored)}")
        self.stdout.write(f"Assets imported: {len(imported)}")

        for action in context.actions:
            self.stdout.write(f"- {action}")