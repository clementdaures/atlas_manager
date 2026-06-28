"""Extract USD Camera from Maya scene"""

from maya import cmds
from maya import OpenMaya as om

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.maya import utils


class USDCamera(ExtractCore):
    """Extract USD Camera from Maya scene - exports the node named 'CAM'."""

    nice_name = "USD Camera"
    color = (100, 200, 255)
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
                },
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
                },
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
                },
            },
        }
        super().__init__(exposed_settings=exposed_settings)

        if not cmds.pluginInfo("mayaUsdPlugin", loaded=True, query=True):
            try:
                cmds.loadPlugin("mayaUsdPlugin")
            except Exception as e:
                om.MGlobal.displayError("Maya USD Plugin cannot be initialized")
                raise e

        om.MGlobal.displayInfo("USD Camera Extractor loaded")

        self._extension = ".usd"
        self.category_functions = {
            "Animation": self._extract_animation,
            "Layout": self._extract_layout,
            "Lighting": self._extract_lighting,
        }

    def _get_camera_node(self):
        """Find and validate the CAM node in the scene."""
        # Search for a node named exactly 'CAM' (with or without namespace)
        matches = cmds.ls("CAM", long=True)

        # Broader search in case it lives inside a namespace (e.g. rig:CAM)
        if not matches:
            all_transforms = cmds.ls(type="transform", long=True)
            matches = [
                n for n in all_transforms
                if n.split("|")[-1].split(":")[-1] == "CAM"
            ]

        if not matches:
            msg = (
                "No node named 'CAM' found in the scene. "
                "Please ensure a camera transform named 'CAM' exists."
            )
            om.MGlobal.displayError(msg)
            raise RuntimeError(msg)

        cam_node = matches[0]

        # Warn if no camera shape is found under this transform
        cam_shapes = cmds.listRelatives(cam_node, shapes=True, type="camera") or []
        if not cam_shapes:
            om.MGlobal.displayWarning(
                f"Node 'CAM' ({cam_node}) does not contain a camera shape — exporting anyway."
            )

        om.MGlobal.displayInfo(f"Found camera node: {cam_node}")
        return cam_node

    def _export_usd(self, file_path, start_frame, end_frame, sub_steps=1):
        """
        Export via mayaUsdPlugin using cmds.file() with type 'USD Export'.
        Settings applied:
          - Animation data ON
          - Up axis Y
          - Linear unit Meters
        """
        cam_node = self._get_camera_node()
        cmds.select(cam_node, replace=True)

        frame_stride = 1.0 / sub_steps if sub_steps > 1 else 1.0

        # Build the options string consumed by the USD Export file translator
        options = ";".join([
            "exportUVs=0",
            "exportSkels=none",
            "exportSkin=none",
            "exportBlendShapes=0",
            "exportDisplayColor=0",
            "exportColorSets=0",
            "mergeTransformAndShape=1",
            "exportInstances=1",
            "exportVisibility=1",
            "animation=1",
            f"startTime={start_frame}",
            f"endTime={end_frame}",
            f"frameStride={frame_stride}",
            "upAxis=y",
            "unit=c",
        ])

        cmds.file(
            file_path,
            force=True,
            exportSelected=True,
            type="USD Export",
            options=options,
        )

        om.MGlobal.displayInfo(f"Exported CAM to {file_path}")

    def _extract_animation(self):
        """Export for Animation category."""
        settings = self.settings.get("Animation")
        _file_path = self.resolve_output()
        _start_frame = settings.get("start_frame")
        _end_frame = settings.get("end_frame")
        sub_steps = settings.get("sub_steps")

        self._export_usd(_file_path, _start_frame, _end_frame, sub_steps)

    def _extract_layout(self):
        """Export for Layout category."""
        settings = self.settings.get("Layout")
        _file_path = self.resolve_output()
        _start_frame = settings.get("start_frame")
        _end_frame = settings.get("end_frame")

        self._export_usd(_file_path, _start_frame, _end_frame)

    def _extract_lighting(self):
        """Export for Lighting category — reuses Layout settings."""
        self._extract_layout()

    def _extract_default(self):
        """Fallback export for any non-specified category."""
        _file_path = self.resolve_output()
        _ranges = utils.get_ranges()
        self._export_usd(_file_path, _ranges[0], _ranges[3])