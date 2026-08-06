"""Validate the files and metadata included in built distributions."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

REQUIRED_SUFFIXES = {
    "__init__.py",
    "apps.py",
    "models.py",
    "templates/wbr_media/renderers/generic.html",
}


def archive_names(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            return {member.name for member in archive.getmembers()}
    raise ValueError(f"Unsupported distribution: {path}")


def validate(path: Path) -> None:
    names = archive_names(path)
    missing = sorted(
        suffix
        for suffix in REQUIRED_SUFFIXES
        if not any(name.endswith(f"wbr_media/{suffix}") for name in names)
    )
    if missing:
        raise SystemExit(
            f"{path}: missing required package files: {', '.join(missing)}"
        )
    if not any(name.endswith("wbr_media/__init__.py") for name in names):
        raise SystemExit(f"{path}: no wbr_media package files found")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_distribution.py DIST_DIR")
    directory = Path(sys.argv[1])
    distributions = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    if len(distributions) != 2:
        raise SystemExit("expected exactly one wheel and one source distribution")
    for distribution in distributions:
        validate(distribution)
        print(f"validated {distribution.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
