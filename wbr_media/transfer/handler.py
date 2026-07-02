from ..models import ImageMetadata, MediaAsset

class MediaImportError(Exception):
    pass


class MediaExportHandler:
    app_label = "wbr_media"
    dependencies = []

    def validate(self, payload, context=None):
        raise NotImplementedError

    def export_data(self, site=None, context=None):
        raise NotImplementedError

    def import_data(self, payload, context=None):
        raise NotImplementedError


class WBRMediaHandler(MediaExportHandler):
    app_label = "wbr_media"
    dependencies = ["core"]

    def validate(self, payload, context):
        if not isinstance(payload, dict):
            raise MediaImportError("WBR Media payload must be an object.")

        assets = payload.get("assets", [])
        if assets is not None and not isinstance(assets, list):
            raise MediaImportError("WBR Media assets must be a list.")

        for row in assets:
            if not row.get("file"):
                raise MediaImportError("MediaAsset requires file.")

    def export_data(self, site, context):
        assets = []

        for asset in MediaAsset.objects.all().order_by("file"):
            row = {
                "file": asset.file.name,
                "title": asset.title,
                "alt_text": asset.alt_text,
                "description": asset.description,
                "file_name": asset.file_name,
                "file_size": asset.file_size,
                "mime_type": asset.mime_type,
                "media_type": asset.media_type,
            }

            metadata = getattr(asset, "image_metadata", None)
            if metadata:
                row["image_metadata"] = {
                    "width": metadata.width,
                    "height": metadata.height,
                    "format": metadata.format,
                    "color_mode": metadata.color_mode,
                    "has_alpha": metadata.has_alpha,
                    "dpi_x": metadata.dpi_x,
                    "dpi_y": metadata.dpi_y,
                }

            assets.append(row)

        return {"assets": assets}

    def import_data(self, payload, context):
        imported = []

        for row in payload.get("assets", []):
            file_path = row["file"]

            defaults = {
                "title": row.get("title", ""),
                "alt_text": row.get("alt_text", ""),
                "description": row.get("description", ""),
                "file_name": row.get("file_name", ""),
                "file_size": row.get("file_size"),
                "mime_type": row.get("mime_type", ""),
                "media_type": row.get("media_type", ""),
            }

            asset = MediaAsset.objects.filter(file=file_path).first()

            if asset:
                MediaAsset.objects.filter(pk=asset.pk).update(**defaults)
                asset.refresh_from_db()
                created = False
            else:
                asset = MediaAsset(file=file_path, **defaults)
                MediaAsset.objects.bulk_create([asset])
                asset = MediaAsset.objects.get(file=file_path)
                created = True

            self.import_image_metadata(asset, row.get("image_metadata"))

            imported.append(asset)
            context.actions.append(
                f"{'Created' if created else 'Updated'} MediaAsset: {asset.file.name}"
            )

        return imported

    def import_image_metadata(self, asset, payload):
        if not payload:
            ImageMetadata.objects.filter(media=asset).delete()
            return

        ImageMetadata.objects.update_or_create(
            media=asset,
            defaults={
                "width": payload["width"],
                "height": payload["height"],
                "format": payload.get("format", ""),
                "color_mode": payload.get("color_mode", ""),
                "has_alpha": payload.get("has_alpha", False),
                "dpi_x": payload.get("dpi_x"),
                "dpi_y": payload.get("dpi_y"),
            },
        )