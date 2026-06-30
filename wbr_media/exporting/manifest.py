from __future__ import annotations

from pathlib import Path

MEDIA_MANIFEST_VERSION = 1
MEDIA_MANIFEST_FILENAME = "media_manifest.json"


def asset_to_manifest_row(asset, files_dir: Path) -> dict:
    storage_path = asset.file.name

    return {
        "file": storage_path,
        "export_path": str(Path("files") / storage_path),
        "exists": asset.file.storage.exists(storage_path),
    }


def build_manifest(*, assets, files_dir: Path) -> dict:
    return {
        "version": MEDIA_MANIFEST_VERSION,
        "assets": [
            asset_to_manifest_row(asset, files_dir)
            for asset in assets
        ],
    }