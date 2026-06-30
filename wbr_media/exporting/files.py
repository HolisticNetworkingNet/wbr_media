from dataclasses import dataclass
from pathlib import Path
import json

from wbr_media.models import MediaAsset
from .manifest import MEDIA_MANIFEST_FILENAME, build_manifest


@dataclass
class MediaExportResult:
    output_directory: Path
    files_directory: Path
    manifest_path: Path
    assets: list[MediaAsset]


class MediaFileExporter:
    def __init__(self, site, output_dir):
        self.site = site
        self.output_dir = Path(output_dir)
        self.files_dir = self.output_dir / "files"

    def run(self):
        self.prepare_output_directory()
        self.assets = self.discover_assets()
        self.write_manifest()
        self.export_assets()
        return self.build_result()

    def prepare_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def build_result(self):
        return MediaExportResult(
            output_directory=self.output_dir,
            files_directory=self.files_dir,
            manifest_path=self.manifest_path,
            assets=self.assets,
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
            json.dumps(manifest, indent=2),
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
            destination.write_bytes(source.read())