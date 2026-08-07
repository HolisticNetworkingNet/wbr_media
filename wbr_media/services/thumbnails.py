"""Generate image renditions from configured WBR Media profiles."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

from wbr_media.config import get_image_profiles
from wbr_media.services.storage import collision_name, rendition_name


def _output_format(source, profile):
    configured = profile.get("format")
    if configured:
        extension = configured.lower().lstrip(".")
        return configured.upper(), f".{extension}"

    image_format = source.format or "JPEG"
    extension = "." + image_format.lower()
    return image_format, extension


def _render(source, profile):
    width = profile["width"]
    height = profile["height"]
    fit = profile.get("fit", "crop")
    upscale = profile.get("upscale", False)
    target = (width, height)

    if fit == "crop":
        if not upscale:
            target = (min(width, source.width), min(height, source.height))
        return ImageOps.fit(
            source,
            target,
            method=Image.Resampling.LANCZOS,
            centering=_centering(profile.get("position", "center")),
        )

    if fit == "scale":
        image = source.copy()
        if not upscale:
            target = (min(width, source.width), min(height, source.height))
        image.thumbnail(target, Image.Resampling.LANCZOS)
        return image

    if fit == "contain":
        contained = ImageOps.contain(source, target, Image.Resampling.LANCZOS)
        if not upscale:
            contained = ImageOps.contain(
                source,
                (min(width, source.width), min(height, source.height)),
                Image.Resampling.LANCZOS,
            )
        background = (0, 0, 0, 0) if "A" in source.getbands() else "white"
        canvas = Image.new(source.mode, target, background)
        canvas.paste(
            contained,
            ((width - contained.width) // 2, (height - contained.height) // 2),
        )
        return canvas

    raise ValueError(f"Unsupported image fit mode: {fit}")


def _centering(position):
    positions = {
        "center": (0.5, 0.5),
        "top": (0.5, 0.0),
        "bottom": (0.5, 1.0),
        "left": (0.0, 0.5),
        "right": (1.0, 0.5),
    }
    if isinstance(position, tuple | list) and len(position) == 2:
        return tuple(float(value) for value in position)
    return positions.get(position, positions["center"])


def generate_renditions(asset):
    """Generate configured image renditions for a saved image asset."""

    if not asset or asset.media_type != "image" or not asset.file:
        return []

    generated = []
    profiles = get_image_profiles()
    dimension_counts = {}
    for profile in profiles.values():
        dimensions = (profile["width"], profile["height"])
        dimension_counts[dimensions] = dimension_counts.get(dimensions, 0) + 1

    asset.file.open("rb")
    try:
        with Image.open(asset.file) as source:
            source.load()
            generated_paths = set()
            for profile_name, profile in profiles.items():
                rendered = _render(source, profile)
                image_format, extension = _output_format(source, profile)
                dimensions = (profile["width"], profile["height"])
                output_path = rendition_name(
                    asset.file.name, rendered.width, rendered.height, extension
                )
                if dimension_counts[dimensions] > 1:
                    output_path = collision_name(output_path, profile_name)
                if output_path in generated_paths:
                    output_path = collision_name(output_path, profile_name)
                output = BytesIO()
                save_options = {}
                if profile.get("quality") is not None:
                    save_options["quality"] = profile["quality"]
                rendered.save(output, format=image_format, **save_options)
                if default_storage.exists(output_path):
                    default_storage.delete(output_path)
                default_storage.save(output_path, ContentFile(output.getvalue()))
                generated_paths.add(output_path)
                generated.append(output_path)
    finally:
        asset.file.close()

    return generated


def resolve_rendition(asset, profile_name):
    """Resolve a generated rendition, returning None when it is unavailable."""

    if not asset or asset.media_type != "image" or not asset.file:
        return None

    profiles = get_image_profiles()
    profile = profiles.get(profile_name)
    if profile is None:
        return None

    dimension_counts = {}
    for configured in profiles.values():
        dimensions = (configured["width"], configured["height"])
        dimension_counts[dimensions] = dimension_counts.get(dimensions, 0) + 1

    asset.file.open("rb")
    try:
        with Image.open(asset.file) as source:
            source.load()
            rendered = _render(source, profile)
            _, extension = _output_format(source, profile)
            path = rendition_name(
                asset.file.name, rendered.width, rendered.height, extension
            )
            dimensions = (profile["width"], profile["height"])
            if dimension_counts[dimensions] > 1:
                path = collision_name(path, profile_name)
    except Exception:
        return None
    finally:
        asset.file.close()

    if not default_storage.exists(path):
        return None

    return {
        "name": profile_name,
        "path": path,
        "url": default_storage.url(path),
        "width": rendered.width,
        "height": rendered.height,
    }


def remove_renditions(filename):
    """Remove generated renditions associated with an original filename."""

    if not filename:
        return
    path = Path(filename)
    directory = str(path.parent)
    prefix = f"{path.stem}-"
    try:
        files = default_storage.listdir(directory)[1]
    except FileNotFoundError:
        return

    for candidate in files:
        if candidate.startswith(prefix):
            default_storage.delete(str(Path(directory) / candidate))
