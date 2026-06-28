"""Extract all Textures."""

from pathlib import Path
import mari

from atlas_manager.dcc.extract_core import ExtractCore


class TextureBundle(ExtractCore):
    """Extract all Textures."""

    nice_name = "Texture Bundle"
    color = (68, 0, 255)
    bundled = True
    bundle_match_id = 8004

    def __init__(self):
        super(TextureBundle, self).__init__()

        self.extension = ".exr"

    def collect(self):
        """Collect geometries."""
        return mari.geo.list()


    def _extract_default(self):
        """Extract method for any non-specified category"""
        _str_directory = self.resolve_output()
        bundle_directory = Path(_str_directory)
        bundle_directory.mkdir(parents=True, exist_ok=True)
        export_items = []

        project_name = mari.projects.current().name()

        for geo in self.collect():
            channels = geo.channelList()
            for channel in channels:
                export_item = mari.ExportItem()
                export_item.setSourceNode(channel.channelNode())
                export_item.setFileTemplate(f"{project_name}_$CHANNEL_$ENTITY.$UDIM.exr")
                export_items.append(export_item)
                mari.exports.addExportItem(export_item, geo)

        mari.exports.exportTextures(export_items, bundle_directory.as_posix(), ShowProgressDialog=True)