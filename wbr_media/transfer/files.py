from dataclasses import dataclass
from pathlib import Path
import json

from wbr_media.models import MediaAsset
from .manifest import MEDIA_MANIFEST_FILENAME, build_manifest
import hashlib
from zipfile import ZIP_DEFLATED, ZipFile

def sha256_zip_member(archive: ZipFile, name: str) -> str:
    h = hashlib.sha256()

    with archive.open(name, "r") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


@dataclass
class MediaExportResult:
    output_directory: Path
    files_directory: Path
    manifest_path: Path
    zip_path: Path
    assets: list[MediaAsset]
    validation_errors: list[str]


@dataclass
class MediaImportPlan:
    zip_path: Path
    manifest: dict
    archive_paths: set[str]
    assets: list[dict]
    validation_errors: list[str]

    @property
    def is_valid(self):
        return not self.validation_errors


class MediaFileExporter:
    def __init__(self, site, output_dir):
        self.site = site
        self.output_dir = Path(output_dir)
        self.files_dir = self.output_dir / "files"
        self.validation_errors = []

    def run(self):
        self.prepare_output_directory()
        self.assets = self.discover_assets()
        self.export_assets()
        self.write_manifest()
        self.create_zip()
        self.validate_zip()
        return self.build_result()

    def prepare_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def build_result(self):
        return MediaExportResult(
            output_directory=self.output_dir,
            files_directory=self.files_dir,
            manifest_path=self.manifest_path,
            zip_path=self.zip_path,
            assets=self.assets,
            validation_errors=self.validation_errors,
        )

    def discover_assets(self):
        return MediaAsset.objects.all().order_by("file")

    def write_manifest(self):
        self.manifest_path = self.output_dir / MEDIA_MANIFEST_FILENAME
        manifest = build_manifest(
            assets=self.assets,
            files_dir=self.files_dir,
        )
        self.manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def export_assets(self):
        for asset in self.assets:
            self.export_asset(asset)

    def export_asset(self, asset):
        if not asset.file.storage.exists(asset.file.name):
            return

        relative_path = Path(asset.file.name)
        destination = self.files_dir / relative_path

        destination.parent.mkdir(parents=True, exist_ok=True)

        with asset.file.open("rb") as source:
            with destination.open("wb") as target:
                for chunk in source.chunks():
                    target.write(chunk)

    def create_zip(self):
        self.zip_path = self.output_dir / "media_export.zip"

        with ZipFile(self.zip_path, "w", ZIP_DEFLATED) as archive:
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file() and file_path != self.zip_path:
                    archive.write(
                        file_path,
                        file_path.relative_to(self.output_dir).as_posix(),
                    )

    def validate_zip(self):
        self.validation_errors = []

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        expected = {
            row["export_path"]: row
            for row in manifest.get("assets", [])
            if row.get("exists")
        }

        expected_paths = set(expected)
        expected_paths.add(MEDIA_MANIFEST_FILENAME)

        with ZipFile(self.zip_path, "r") as archive:
            actual_paths = set(archive.namelist())

            for path in sorted(expected_paths - actual_paths):
                self.validation_errors.append(f"Missing from zip: {path}")

            for path in sorted(actual_paths - expected_paths):
                self.validation_errors.append(f"Unexpected file in zip: {path}")

            for path in sorted(expected_paths & actual_paths):
                if path == MEDIA_MANIFEST_FILENAME:
                    continue

                expected_checksum = expected[path].get("sha256")
                actual_checksum = sha256_zip_member(archive, path)

                if actual_checksum != expected_checksum:
                    self.validation_errors.append(
                        f"Checksum mismatch for {path}: "
                        f"expected {expected_checksum}, got {actual_checksum}"
                    )


class MediaFileImporter:
    def __init__(self, zip_path):
        self.zip_path = Path(zip_path)
        self.validation_errors = []

    def inspect(self):
        self.validation_errors = []

        if not self.zip_path.exists():
            self.validation_errors.append(f"Zip file does not exist: {self.zip_path}")

            return MediaImportPlan(
                zip_path=self.zip_path,
                manifest={},
                archive_paths=set(),
                assets=[],
                validation_errors=self.validation_errors,
            )

        with ZipFile(self.zip_path, "r") as archive:
            archive_paths = set(archive.namelist())

            if MEDIA_MANIFEST_FILENAME not in archive_paths:
                self.validation_errors.append(
                    f"Missing manifest: {MEDIA_MANIFEST_FILENAME}"
                )

                return MediaImportPlan(
                    zip_path=self.zip_path,
                    manifest={},
                    archive_paths=archive_paths,
                    assets=[],
                    validation_errors=self.validation_errors,
                )

            manifest = json.loads(
                archive.read(MEDIA_MANIFEST_FILENAME).decode("utf-8")
            )

            self.validate_archive(archive, manifest, archive_paths)

        return MediaImportPlan(
            zip_path=self.zip_path,
            manifest=manifest,
            archive_paths=archive_paths,
            assets=manifest.get("assets", []),
            validation_errors=self.validation_errors,
        )

    def validate_archive(self, archive, manifest, archive_paths):
        expected = {
            row["export_path"]: row
            for row in manifest.get("assets", [])
            if row.get("exists")
        }

        expected_paths = set(expected)
        expected_paths.add(MEDIA_MANIFEST_FILENAME)

        for path in sorted(expected_paths - archive_paths):
            self.validation_errors.append(f"Missing from zip: {path}")

        for path in sorted(archive_paths - expected_paths):
            self.validation_errors.append(f"Unexpected file in zip: {path}")

        for path in sorted(expected_paths & archive_paths):
            if path == MEDIA_MANIFEST_FILENAME:
                continue

            expected_checksum = expected[path].get("sha256")
            actual_checksum = sha256_zip_member(archive, path)

            if actual_checksum != expected_checksum:
                self.validation_errors.append(
                    f"Checksum mismatch for {path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )