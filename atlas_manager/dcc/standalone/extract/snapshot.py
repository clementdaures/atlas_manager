from pathlib import Path
import shutil

from atlas_manager.dcc.extract_core import ExtractCore

class Snapshot(ExtractCore):
    """Snapshot the work file"""

    nice_name = "Snapshot"
    color = (255, 255, 255)

    def __init__(self):
        super().__init__()
        self._source_path = None

    @property
    def source_path(self):
        return self._source_path

    @source_path.setter
    def source_path(self, val):
        self._source_path = val

    def _extract_default(self):
        """Extract method for any non-specified category"""
        _file_path = self.resolve_output()
        shutil.copyfile(self._source_path, _file_path)
        return _file_path