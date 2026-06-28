"""Extract Alembic from Houdini scene - Selection Only"""

import logging

import hou

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class Alembic(ExtractCore):
    """Extract Alembic from Houdini scene - Selection Only."""

    nice_name = "Alembic Selection"
    color = (244, 132, 132)
    optional = True

    def __init__(self):
        _ranges = utils.get_ranges()

        exposed_settings = {
            "Animation": {
                "start_frame": {
                    "display_name": "Start Frame",
                    "type": "integer",
                    "value": _ranges[0],
                },
                "end_frame": {
                    "display_name": "End Frame",
                    "type": "integer",
                    "value": _ranges[3],
                },
                "sub_steps": {
                    "display_name": "Sub Steps",
                    "type": "integer",
                    "value": 1,
                }
            },
            "Fx": {
                "start_frame": {
                    "display_name": "Start Frame",
                    "type": "integer",
                    "value": _ranges[0],
                },
                "end_frame": {
                    "display_name": "End Frame",
                    "type": "integer",
                    "value": _ranges[3],
                },
                "sub_steps": {
                    "display_name": "Sub Steps",
                    "type": "integer",
                    "value": 1,
                }
            },
            "Layout": {
                "start_frame": {
                    "display_name": "Start Frame",
                    "type": "integer",
                    "value": _ranges[0],
                },
                "end_frame": {
                    "display_name": "End Frame",
                    "type": "integer",
                    "value": _ranges[3],
                }
            },
            "Lighting": {
                "start_frame": {
                    "display_name": "Start Frame",
                    "type": "integer",
                    "value": _ranges[0],
                },
                "end_frame": {
                    "display_name": "End Frame",
                    "type": "integer",
                    "value": _ranges[3],
                }
            }
        }
        super().__init__(exposed_settings=exposed_settings)

        if hou.isApprentice():
            msg = "Alembic export is not supported in Houdini Apprentice."
            self._message = msg
            self._enabled = False
            self._state = "unavailable"

        self._extension = ".abc"
        self.category_functions = {
            "Model": self._extract_model,
            "Animation": self._extract_animation,
            "Fx": self._extract_fx,
            "Layout": self._extract_layout,
            "Lighting": self._extract_lighting,
        }

    def _get_selected_nodes(self):
        """Get selected nodes and validate selection."""
        selected_nodes = hou.selectedNodes()

        if not selected_nodes:
            msg = "No nodes selected. Please select nodes to export."
            LOG.error(msg)
            raise RuntimeError(msg)

        # Filter for valid node types (geometry, transforms)
        valid_nodes = []
        for node in selected_nodes:
            # Accept nodes from /obj context
            if node.path().startswith("/obj/"):
                valid_nodes.append(node)

        if not valid_nodes:
            msg = "No valid nodes selected. Please select nodes from /obj context."
            LOG.error(msg)
            raise RuntimeError(msg)

        LOG.info(f"Exporting {len(valid_nodes)} selected node(s)")
        return valid_nodes

    def _check_for_rop_alembic(self):
        """Check if any selected node is a ROP Alembic node."""
        selected_nodes = hou.selectedNodes()

        for node in selected_nodes:
            if node.type().name() == "rop_alembic":
                return node
        return None

    def _extract_with_rop(self, rop_node):
        """Use existing ROP Alembic node with auto-filled path."""
        _file_path = self.resolve_output()

        # Set the output path
        rop_node.parm("filename").set(_file_path)

        LOG.info(f"Using ROP Alembic node: {rop_node.path()}")
        LOG.info(f"Output path set to: {_file_path}")

        # Render
        rop_node.render()
        LOG.info(f"Exported using ROP to {_file_path}")
        return True

    def _extract_with_nodes(self, selected_nodes, start_frame=None, end_frame=None, sub_steps=1):
        """Extract selected nodes using temporary ROP."""
        _file_path = self.resolve_output()
        root_node = hou.node("/obj")
        step = float(1.0 / sub_steps)

        # Create temporary export geo node
        export_geo = root_node.createNode("geo", node_name="__atlas_export_selection")

        try:
            # Delete default nodes inside
            try:
                export_geo.allSubChildren()[0].destroy()
            except IndexError:
                pass

            # Create object merge for each selected node
            merge_node = export_geo.createNode("object_merge")
            merge_node.parm("numobj").set(len(selected_nodes))
            merge_node.parm("xformtype").set("local")
            merge_node.parm("pack").set(True)

            for idx, node in enumerate(selected_nodes):
                parameter = f"objpath{idx + 1}"
                merge_node.parm(parameter).set(node.path())

            # Create ROP Alembic
            rop_sop = export_geo.createNode("rop_alembic")
            rop_sop.setInput(0, merge_node)
            rop_sop.parm("filename").set(_file_path)

            # Set frame range if provided
            if start_frame is not None and end_frame is not None:
                rop_sop.parm("trange").set("normal")
                rop_sop.parm("f1").deleteAllKeyframes()
                rop_sop.parm("f2").deleteAllKeyframes()
                rop_sop.parm("f1").set(start_frame)
                rop_sop.parm("f2").set(end_frame)
                rop_sop.parm("f3").set(step)
            else:
                rop_sop.parm("trange").set("off")

            # Set export properties
            rop_sop.parm("shape_nodes").set(True)
            rop_sop.parm("use_instancing").set(True)
            rop_sop.parm("shutter1").set(0)
            rop_sop.parm("shutter2").set(1)
            rop_sop.parm("motionBlur").set(False)
            rop_sop.parm("save_attributes").set(True)
            rop_sop.parm("samples").set(2)
            rop_sop.parm("facesets").set("nonempty")

            # Render
            rop_sop.render()
            LOG.info(f"Exported selection to {_file_path}")

        finally:
            # Clean up temporary node
            export_geo.destroy()

        return True

    def _extract_model(self):
        """Extract method for model category"""
        # Check if a ROP Alembic is selected
        rop_node = self._check_for_rop_alembic()
        if rop_node:
            return self._extract_with_rop(rop_node)

        # Otherwise, use selected nodes
        selected_nodes = self._get_selected_nodes()
        return self._extract_with_nodes(selected_nodes)

    def _extract_animation(self):
        """Extract method for animation category"""
        # Check if a ROP Alembic is selected
        rop_node = self._check_for_rop_alembic()
        if rop_node:
            # Still need to set frame range from settings
            settings = self.settings.get("Animation")
            _start_frame = settings.get_property("start_frame")
            _end_frame = settings.get_property("end_frame")
            sub_steps = settings.get_property("sub_steps")
            step = float(1.0 / sub_steps)

            rop_node.parm("trange").set("normal")
            rop_node.parm("f1").set(_start_frame)
            rop_node.parm("f2").set(_end_frame)
            rop_node.parm("f3").set(step)

            return self._extract_with_rop(rop_node)

        # Otherwise, use selected nodes
        settings = self.settings.get("Animation")
        _start_frame = settings.get_property("start_frame")
        _end_frame = settings.get_property("end_frame")
        sub_steps = settings.get_property("sub_steps")

        selected_nodes = self._get_selected_nodes()
        return self._extract_with_nodes(selected_nodes, _start_frame, _end_frame, sub_steps)

    def _extract_fx(self):
        """Extract method for fx category"""
        return self._extract_animation()

    def _extract_layout(self):
        """Extract method for layout category"""
        # Check if a ROP Alembic is selected
        rop_node = self._check_for_rop_alembic()
        if rop_node:
            settings = self.settings.get("Layout")
            _start_frame = settings.get_property("start_frame")
            _end_frame = settings.get_property("end_frame")

            rop_node.parm("trange").set("normal")
            rop_node.parm("f1").set(_start_frame)
            rop_node.parm("f2").set(_end_frame)

            return self._extract_with_rop(rop_node)

        settings = self.settings.get("Layout")
        _start_frame = settings.get_property("start_frame")
        _end_frame = settings.get_property("end_frame")

        selected_nodes = self._get_selected_nodes()
        return self._extract_with_nodes(selected_nodes, _start_frame, _end_frame)

    def _extract_lighting(self):
        """Extract method for lighting category"""
        return self._extract_layout()

    def _extract_default(self):
        """Extract method for any non-specified category"""
        # Check if a ROP Alembic is selected
        rop_node = self._check_for_rop_alembic()
        if rop_node:
            return self._extract_with_rop(rop_node)

        selected_nodes = self._get_selected_nodes()
        return self._extract_with_nodes(selected_nodes)