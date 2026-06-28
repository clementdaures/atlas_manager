"""Extract Alembic bundle from Houdini scene"""

import logging
from pathlib import Path

import hou

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class AlembicBundled(ExtractCore):
    """Extract multiple Alembics from Houdini scene into a bundle"""

    nice_name = "Alembic Bundled"
    color = (180, 255, 100)
    bundled = True
    optional = True
    bundle_match_id = 8001  # Unique ID to match with ingestor

    def __init__(self):
        _ranges = utils.get_ranges()

        # Find all ROP Alembic nodes in the scene
        rop_alembic_nodes = []
        for node in hou.node("/").allSubChildren():
            if node.type().name() == "rop_alembic":
                rop_alembic_nodes.append(node)

        # Get ROP names for the UI list
        rop_items = [node.path() for node in rop_alembic_nodes]

        global_exposed_settings = {
            "start_frame": {"display_name": "Start Frame", "type": "integer", "value": _ranges[0]},
            "end_frame": {"display_name": "End Frame", "type": "integer", "value": _ranges[3]},
            "sub_steps": {"display_name": "Sub Steps", "type": "integer", "value": 1},
            "rop_nodes": {
                "display_name": "ROP Alembic Nodes to Export",
                "type": "list",
                "value": rop_items,
            },
        }

        super().__init__(global_exposed_settings=global_exposed_settings)

        if hou.isApprentice():
            msg = "Alembic export is not supported in Houdini Apprentice."
            LOG.error(msg)
            self._message = msg
            self._enabled = False
            self._state = "unavailable"

        self.extension = ".abc"

    def _extract_default(self):
        """Bundle multiple Alembics from existing ROP Alembic nodes"""
        _start = self.global_settings.get("start_frame")
        _end = self.global_settings.get("end_frame")
        sub_steps = self.global_settings.get("sub_steps")
        selected_rop_paths = self.global_settings.get("rop_nodes")

        bundle_dir = Path(self.resolve_output())
        bundle_dir.mkdir(parents=True, exist_ok=True)

        _bundle_info = {}

        step = float(1.0 / sub_steps)

        for rop_path in selected_rop_paths:
            rop_node = hou.node(rop_path)
            if not rop_node:
                LOG.warning(f"ROP node {rop_path} not found, skipping...")
                continue

            if rop_node.type().name() != "rop_alembic":
                LOG.warning(f"Node {rop_path} is not a ROP Alembic node, skipping...")
                continue

            geo_name = rop_node.name()

            # Create safe filename based on geometry node name
            safe_name = geo_name.replace(":", "_").replace("|", "_").replace("/", "_")
            _file_path = bundle_dir / f"{safe_name}.abc"

            try:
                # Store original settings
                original_filename = rop_node.parm("filename").eval()
                original_trange = rop_node.parm("trange").eval()
                original_f1 = rop_node.parm("f1").eval()
                original_f2 = rop_node.parm("f2").eval()
                original_f3 = rop_node.parm("f3").eval()

                # Update ROP settings for bundle export
                rop_node.parm("filename").set(str(_file_path))
                rop_node.parm("trange").set("normal")
                rop_node.parm("f1").deleteAllKeyframes()
                rop_node.parm("f2").deleteAllKeyframes()
                rop_node.parm("f1").set(_start)
                rop_node.parm("f2").set(_end)
                rop_node.parm("f3").set(step)

                # Render
                rop_node.render()
                LOG.info(f"Exported {geo_name} from {rop_path} to {_file_path}")

                _bundle_info[geo_name] = {
                    "extension": ".abc",
                    "path": str(_file_path),
                    "sequential": False,
                    "source_rop": rop_path,
                }

                # Restore original settings
                rop_node.parm("filename").set(original_filename)
                rop_node.parm("trange").set(original_trange)
                rop_node.parm("f1").set(original_f1)
                rop_node.parm("f2").set(original_f2)
                rop_node.parm("f3").set(original_f3)

            except Exception as e:
                LOG.error(f"Failed to export from ROP {rop_path}: {e}")

        self.bundle_info = _bundle_info