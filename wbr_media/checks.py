"""Django system checks for WBR Media configuration."""

from django.core import checks

from .config import IMAGE_PROFILE_FITS, IMAGE_PROFILE_KEYS, get_image_profiles


@checks.register(checks.Tags.models)
def check_image_profiles(app_configs, **kwargs):
    errors = []
    profiles = get_image_profiles()

    if not isinstance(profiles, dict):
        return [
            checks.Error(
                "WBR_MEDIA['IMAGE_PROFILES'] must be a mapping of names to profiles.",
                id="wbr_media.E001",
            )
        ]

    fingerprints = {}
    for name, profile in profiles.items():
        prefix = f"WBR_MEDIA['IMAGE_PROFILES']['{name}']"
        if not isinstance(name, str) or not name:
            errors.append(
                checks.Error(
                    "Image profile names must be non-empty strings.",
                    id="wbr_media.E002",
                )
            )
            continue
        if not isinstance(profile, dict):
            errors.append(
                checks.Error(
                    f"{prefix} must be a mapping.",
                    id="wbr_media.E003",
                )
            )
            continue

        unknown = set(profile) - IMAGE_PROFILE_KEYS
        if unknown:
            errors.append(
                checks.Error(
                    f"{prefix} contains unsupported keys: {', '.join(sorted(unknown))}.",
                    id="wbr_media.E004",
                )
            )

        for dimension in ("width", "height"):
            value = profile.get(dimension)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(
                    checks.Error(
                        f"{prefix}['{dimension}'] must be a positive integer.",
                        id="wbr_media.E005",
                    )
                )

        fit = profile.get("fit", "crop")
        if fit not in IMAGE_PROFILE_FITS:
            errors.append(
                checks.Error(
                    f"{prefix}['fit'] must be one of: {', '.join(sorted(IMAGE_PROFILE_FITS))}.",
                    id="wbr_media.E006",
                )
            )

        quality = profile.get("quality")
        if quality is not None and (
            not isinstance(quality, int)
            or isinstance(quality, bool)
            or not 1 <= quality <= 100
        ):
            errors.append(
                checks.Error(
                    f"{prefix}['quality'] must be an integer from 1 to 100.",
                    id="wbr_media.E007",
                )
            )

        if "upscale" in profile and not isinstance(profile["upscale"], bool):
            errors.append(
                checks.Error(
                    f"{prefix}['upscale'] must be a boolean.",
                    id="wbr_media.E008",
                )
            )

        fingerprint = tuple(
            (key, profile.get(key, "crop" if key == "fit" else None))
            for key in sorted(IMAGE_PROFILE_KEYS)
        )
        if fingerprint in fingerprints:
            errors.append(
                checks.Warning(
                    f"{prefix} duplicates image profile '{fingerprints[fingerprint]}'.",
                    hint="Remove one profile or keep it as an intentional alias.",
                    id="wbr_media.W001",
                )
            )
        else:
            fingerprints[fingerprint] = name

    return errors
