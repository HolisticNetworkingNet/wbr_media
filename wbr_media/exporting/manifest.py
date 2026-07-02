from __future__ import annotations

from pathlib import Path

MEDIA_MANIFEST_VERSION = 1
MEDIA_MANIFEST_FILENAME = "media_manifest.json"


def asset_to_manifest_row(asset, files_dir: Path) -> dict:
    storage_path = asset.file.name
    export_path = Path("files") / storage_path
    exported_file = files_dir / storage_path
    exists = exported_file.exists()

    row = {
        "file": storage_path,
        "export_path": str(export_path),
        "exists": exists,
    }

    if exists:
        row["size_bytes"] = exported_file.stat().st_size

    return row


def build_manifest(*, assets, files_dir: Path) -> dict:
    return {
        "version": MEDIA_MANIFEST_VERSION,
        "assets": [
            asset_to_manifest_row(asset, files_dir)
            for asset in assets
        ],
    }