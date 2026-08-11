import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("demo", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="page",
            name="thumbnail_media",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="thumbnail_pages",
                to="wbr_media.mediaasset",
            ),
        )
    ]
