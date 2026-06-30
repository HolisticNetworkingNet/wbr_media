class MediaFileExporter:
    def __init__(self, site=None, output_dir=None):
        self.site = site
        self.output_dir = output_dir

    def run(self):
        raise NotImplementedError