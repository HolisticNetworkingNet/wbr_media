from pathlib import Path
from dataclasses import dataclass
from pathlib import Path


class MediaFileExporter:
    def __init__(self, site, output_dir):
        self.site = site
        self.output_dir = Path(output_dir)

    def run(self):
        self.prepare_output_directory()
        return self.build_result()

    def prepare_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_result(self):
        return MediaExportResult(
            output_directory=self.output_dir,
        )


@dataclass
class MediaExportResult:
    output_directory: Path