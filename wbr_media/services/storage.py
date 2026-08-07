"""Storage naming helpers for generated WBR Media renditions."""

from pathlib import Path


def rendition_name(
    original_name,
    width,
    height,
    extension,
    profile_name=None,
):
    """Build a readable rendition path from the original storage path."""

    original = Path(original_name)
    profile_suffix = f"-{profile_name}" if profile_name else ""
    extension = extension if extension.startswith(".") else f".{extension}"
    return str(
        original.with_name(
            f"{original.stem}{profile_suffix}-{width}x{height}{extension}"
        )
    )


def collision_name(path, profile_name):
    """Add a profile name to a dimension-only rendition path."""

    rendition = Path(path)
    return str(
        rendition.with_name(
            f"{rendition.stem.rsplit('-', 1)[0]}-{profile_name}"
            f"-{rendition.stem.rsplit('-', 1)[-1]}{rendition.suffix}"
        )
    )
