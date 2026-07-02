from __future__ import annotations
import hashlib

from pathlib import Path

MEDIA_MANIFEST_VERSION = 1
MEDIA_MANIFEST_FILENAME = "media_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def asset_to_manifest_row(asset, files_dir: Path) -> dict:
    storage_path = asset.file.name
    exported_file = files_dir / storage_path
    exists = exported_file.exists()

    row = {
        "file": storage_path,
        "export_path": str(Path("files") / storage_path),
        "exists": exists,
    }

    if exists:
        row["size_bytes"] = exported_file.stat().st_size
        row["sha256"] = sha256_file(exported_file)

    return row


def build_manifest(*, assets, files_dir: Path) -> dict:
    return {
        "version": MEDIA_MANIFEST_VERSION,
        "assets": [
            asset_to_manifest_row(asset, files_dir)
            for asset in assets
        ],
    }