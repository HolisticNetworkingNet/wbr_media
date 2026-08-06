"""Configuration helpers for WBR Media."""

from copy import deepcopy

from django.conf import settings

IMAGE_PROFILE_KEYS = {
    "width",
    "height",
    "fit",
    "position",
    "format",
    "quality",
    "upscale",
    "version",
}
IMAGE_PROFILE_FITS = {"crop", "scale", "contain"}


def get_image_profiles():
    """Return the configured image profiles without mutating Django settings."""

    config = getattr(settings, "WBR_MEDIA", {}) or {}
    profiles = config.get("IMAGE_PROFILES", {}) or {}
    return deepcopy(profiles)
