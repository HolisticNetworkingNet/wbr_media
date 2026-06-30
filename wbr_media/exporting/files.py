from dataclasses import dataclass
from pathlib import Path


@dataclass
class MediaExportResult:
    output_directory: Path
    files_directory: Path


class MediaFileExporter:
    def __init__(self, site, output_dir):
        self.site = site
        self.output_dir = Path(output_dir)
        self.files_dir = self.output_dir / "files"

    def run(self):
        self.prepare_output_directory()
        return self.build_result()

    def prepare_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def build_result(self):
        return MediaExportResult(
            output_directory=self.output_dir,
            files_directory=self.files_dir,
        )