"""Extract USD from Houdini scene."""

import logging
import json
from pathlib import Path

import hou

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class Usd(ExtractCore):
    """Extract USD from Houdini scene."""

    nice_name = "Usd"
    optional = False
    color = (71, 143, 203)

    def __init__(self):
        _ranges = utils.get_ranges()

        global_exposed_settings = {
            "frame_mode": {
                "display_name": "Frame Mode",
                "type": "combo",
                "items": ["Current Frame", "Custom Range"],
                "value": "Current Frame",
            },
            "start_frame": {
                "display_name": "Start Frame (Custom Range)",
                "type": "integer",
                "value": _ranges[0],
            },
            "end_frame": {
                "display_name": "End Frame (Custom Range)",
                "type": "integer",
                "value": _ranges[3],
            },
        }

        # Sub-steps are only meaningful for Animation/Fx, kept as
        # per-category overrides for those who need them.
        exposed_settings = {
            "Animation": {
                "sub_steps": {
                    "display_name": "Sub Steps",
                    "type": "integer",
                    "value": 1,
                }
            },
            "Fx": {
                "sub_steps": {
                    "display_name": "Sub Steps",
                    "type": "integer",
                    "value": 1,
                }
            },
        }

        super().__init__(
            exposed_settings=exposed_settings,
            global_exposed_settings=global_exposed_settings,
        )

        if hou.isApprentice():
            self._extension = ".usdnc"
            self._message = (
                "USD export is not supported in Houdini Apprentice. "
                "Format will be saved as .usdnc"
            )
        else:
            self._extension = ".usd"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_render_node_recursive(self, parent_node, node_name="OUT_USD"):
        """Recursively search for a node by name in the hierarchy.

        Args:
            parent_node: The parent node to search in.
            node_name: The name of the node to find (default: "OUT_USD").

        Returns:
            hou.Node or None: The found node or None if not found.
        """
        for child in parent_node.children():
            if child.name() == node_name:
                return child

        for child in parent_node.children():
            result = self._find_render_node_recursive(child, node_name)
            if result:
                return result

        return None

    def _find_render_node(self):
        """Find the OUT_USD node anywhere in the scene hierarchy.

        Searches in the following order:
        1. Direct children of /stage
        2. Direct children of /obj
        3. Recursively throughout /obj (including inside geo nodes)
        4. Recursively throughout /stage

        Returns:
            tuple: (node, context, node_type) where:
                - node: The found hou.Node
                - context: 'stage' or 'obj'
                - node_type: 'usd_rop' (for /stage), 'usdexport' (for /obj SOP),
                             or 'usd_rop_obj' (for /obj ROP)

        Raises:
            Exception: If the OUT_USD node is not found anywhere.
        """
        stage_node = hou.node("/stage")
        if stage_node:
            render_usd_node = stage_node.node("OUT_USD")
            if render_usd_node:
                LOG.info(f"Found OUT_USD node at: {render_usd_node.path()}")
                return render_usd_node, "stage", "usd_rop"

        obj_node = hou.node("/obj")
        if obj_node:
            render_usd_node = obj_node.node("OUT_USD")
            if render_usd_node:
                LOG.info(f"Found OUT_USD node at: {render_usd_node.path()}")
                if render_usd_node.type().name() in ["usd_rop", "usd"]:
                    return render_usd_node, "obj", "usd_rop_obj"
                else:
                    return render_usd_node, "obj", "usdexport"

        if obj_node:
            render_usd_node = self._find_render_node_recursive(obj_node, "OUT_USD")
            if render_usd_node:
                LOG.info(f"Found OUT_USD node at: {render_usd_node.path()}")
                node_type_name = render_usd_node.type().name()
                if node_type_name == "usdexport":
                    return render_usd_node, "obj", "usdexport"
                elif node_type_name in ["usd_rop", "usd"]:
                    return render_usd_node, "obj", "usd_rop_obj"
                else:
                    return render_usd_node, "obj", "usdexport"

        if stage_node:
            render_usd_node = self._find_render_node_recursive(stage_node, "OUT_USD")
            if render_usd_node:
                LOG.info(f"Found OUT_USD node at: {render_usd_node.path()}")
                return render_usd_node, "stage", "usd_rop"

        msg = "Node 'OUT_USD' not found anywhere in the scene"
        LOG.error(msg)
        raise Exception(msg)


    def save_frame_range(self, output_file_path):
        """Write (or overwrite) a frame_range.json alongside the given output file.

        Args:
            output_file_path (str): Path to the main output file (e.g. the .usd).
                                    The JSON will be written in the same directory.
        """
        start_frame = self.global_settings.get("start_frame")
        end_frame = self.global_settings.get("end_frame")

        json_path = Path(output_file_path).parent.parent.parent / "live" / "frame_range.json"
        data = {"start_frame": start_frame, "end_frame": end_frame}

        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

        LOG.info(f"Saved frame range {start_frame}-{end_frame} to: {json_path}")


    def __extract_base(self):
        """Convenience method for the shared parts of the extract methods."""
        render_usd_node, context, node_type = self._find_render_node()

        if context == "stage":
            LOG.info(f"Using USD ROP in /stage: {render_usd_node.path()}")
            return None, render_usd_node

        elif context == "obj":
            if node_type == "usdexport":
                LOG.info(f"Using existing usdexport SOP: {render_usd_node.path()}")
                return None, render_usd_node

            elif node_type == "usd_rop_obj":
                LOG.info(f"Using USD ROP in /obj: {render_usd_node.path()}")
                return None, render_usd_node

            else:
                root_node = hou.node("/obj")

                geo_node = root_node.node("__atlas_export_usd")
                if geo_node:
                    geo_node.destroy()

                geo_node = root_node.createNode("geo", node_name="atlas_export_usd")
                try:
                    geo_node.allSubChildren()[0].destroy()
                except IndexError:
                    pass

                merge_node = geo_node.createNode("object_merge")
                merge_node.parm("numobj").set(1)
                merge_node.parm("objpath1").set(render_usd_node.path())
                merge_node.parm("xformtype").set("local")
                merge_node.parm("pack").set(False)

                rop_sop = geo_node.createNode("usdexport")
                rop_sop.setInput(0, merge_node)
                LOG.info(
                    f"Created export setup with object merge from: {render_usd_node.path()}"
                )
                return geo_node, rop_sop

    def __apply_frame_range(self, rop_sop, sub_steps=1):
        """Apply the frame range from global settings to the given ROP node.

        When frame_mode is 'Current Frame', trange is set to 'off' so Houdini
        exports only the currently evaluated frame.  When it is 'Custom Range'
        the start/end values from global settings are used together with the
        provided sub_steps value.

        Args:
            rop_sop: The ROP or SOP node whose frame-range parms will be set.
            sub_steps (int): Number of sub-steps per frame (used in Custom Range
                             mode only). Defaults to 1.
        """
        frame_mode = self.global_settings.get("frame_mode")

        if frame_mode == "Current Frame":
            LOG.info("Frame mode: Current Frame — setting trange to off")
            rop_sop.parm("trange").set("off")
        else:
            start_frame = self.global_settings.get("start_frame")
            end_frame = self.global_settings.get("end_frame")
            step = float(1.0 / max(sub_steps, 1))

            LOG.info(
                f"Frame mode: Custom Range — {start_frame} to {end_frame}, "
                f"sub_steps={sub_steps}, step={step}"
            )
            rop_sop.parm("trange").set("normal")
            rop_sop.parm("f1").deleteAllKeyframes()
            rop_sop.parm("f2").deleteAllKeyframes()
            rop_sop.parm("f1").set(start_frame)
            rop_sop.parm("f2").set(end_frame)
            rop_sop.parm("f3").set(step)


    def _extract_default(self):
        """Extract method for any non-specified category."""
        _file_path = self.resolve_output()
        self.save_frame_range(_file_path)
        geo_node, rop_sop = self.__extract_base()

        rop_sop.parm("lopoutput").set(_file_path)
        self.__apply_frame_range(rop_sop)

        rop_sop.parm("execute").pressButton()
        if geo_node:
            geo_node.destroy()
        return True