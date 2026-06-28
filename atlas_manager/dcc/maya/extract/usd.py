"""Extract Usd Model from Maya scene"""

from maya import cmds
from maya import OpenMaya as om

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.maya import utils


class Usd(ExtractCore):
    """Extract Usd Model from Maya scene - exports the selected group with 'mdl' child."""

    nice_name = "Usd"
    color = (100, 200, 255)
    optional = True

    def __init__(self):
        _ranges = utils.get_ranges()

        global_exposed_settings = {
            "frame_mode": {
                "display_name": "Frame Mode",
                "type": "combo",
                "items": ["Current Frame", "Custom Range"],
                "value": "Current Frame",
            },
            "start_frame": {"display_name": "Start Frame", "type": "integer", "value": _ranges[0]},
            "end_frame":   {"display_name": "End Frame",   "type": "integer", "value": _ranges[3]},
            "sub_steps":   {"display_name": "Sub Steps",   "type": "integer", "value": 1},
        }

        super().__init__(global_exposed_settings=global_exposed_settings)

        if not cmds.pluginInfo("mayaUsdPlugin", loaded=True, query=True):
            try:
                cmds.loadPlugin("mayaUsdPlugin")
            except Exception as e:
                om.MGlobal.displayError("Maya Usd Plugin cannot be initialized")
                raise e

        om.MGlobal.displayInfo("Usd Model Extractor loaded")

        self._extension = ".usd"

    @staticmethod
    def _get_selected_group():
        """Get the selected group and validate it has a 'mdl' child."""
        # Get the current selection
        selection = cmds.ls(selection=True, long=True)

        if not selection:
            msg = "No group selected. Please select a group to export."
            om.MGlobal.displayError(msg)
            raise RuntimeError(msg)

        if len(selection) > 1:
            msg = "Multiple objects selected. Please select only one group to export."
            om.MGlobal.displayError(msg)
            raise RuntimeError(msg)

        group_node = selection[0]

        # Get the short name and convert to uppercase
        short_name = group_node.split("|")[-1].split(":")[-1]
        group_name_upper = short_name.upper()

        # Check if the group has an 'mdl' child
        children = cmds.listRelatives(group_node, children=True, fullPath=True) or []
        mdl_children = []

        category = ["mdl", "cloth",]

        for child in children:
            child_short_name = child.split("|")[-1].split(":")[-1]
            if child_short_name.lower() in category:
                mdl_children.append(child)

        if not mdl_children:
            om.MGlobal.displayWarning(
                f"Selected group '{group_name_upper}' does not contain an 'mdl' child — exporting anyway."
            )
        else:
            om.MGlobal.displayInfo(
                f"Found 'mdl' child under group '{group_name_upper}'"
            )

        om.MGlobal.displayInfo(f"Selected group: {group_name_upper} ({group_node})")
        return group_node

    def _export_usd(self, file_path, start_frame, end_frame, sub_steps=1):
        """
        Export via mayaUsdPlugin using cmds.file() with type 'Usd Export'.
        Settings applied:
          - Animation data ON
          - Up axis Y
          - Linear unit Meters
        """
        group_node = self._get_selected_group()
        cmds.select(group_node, replace=True)

        frame_stride = 1.0 / sub_steps if sub_steps > 1 else 1.0

        # Build the options string consumed by the Usd Export file translator
        options = ";".join([
            # Include Options
            "includeHistory=0",
            "includeChannels=1",
            "includeExpressions=1",
            "includeConstraints=1",
            "includeTextureInfo=0",

            # Output Options
            "rootPrimType=scope",
            "defaultPrim=None",

            # Geometry Options
            "exportMeshes=1",
            "defaultMeshScheme=catmullClark",
            "exportColorSets=0",
            "exportComponentTags=0",
            "exportUVs=1",
            "filterTypes=nurbsCurve",
            "exportSkels=none",
            "exportSkin=none",
            "exportBlendShapes=0",
            "exportDisplayColor=0",

            # Materials Options
            "exportMaterials=0",
            "shadingMode=useRegistry",
            "convertMaterialsTo=[]",
            "exportAssignedMaterials=1",
            "exportRelativeTextures=automatic",

            # Advanced Options
            "exportInstances=1",
            "exportVisibility=0",
            "mergeTransformAndShape=0",
            "includeEmptyTransforms=1",
            "stripNamespaces=1",
            "worldspace=0",
            "exportStagesAsRefs=1",
            "excludeExportTypes=[Models,Lights]",

            # Axis & Unit Conversion
            "upAxis=y",
            "unit=cm",

            # Animation Options
            "animation=1",
            f"startTime={start_frame}",
            f"endTime={end_frame}",
            f"frameStride={frame_stride}",
            "frameSample=",
            "eulerFilter=0",
            "staticSingleSample=0",
            "legacyMaterialScope=0",
        ])

        cmds.file(
            file_path,
            force=True,
            exportSelected=True,
            type="USD Export",
            options=options,
        )

        om.MGlobal.displayInfo(f"Exported selected group to {file_path}")

    def _extract_default(self):
        """Fallback export for any non-specified category."""
        export_mode = self.global_settings.get("export_mode")

        if export_mode == "current_frame":
            _start = _end = int(cmds.currentTime(query=True))
        else:
            _start = self.global_settings.get("start_frame")
            _end = self.global_settings.get("end_frame")

        _file_path = self.resolve_output()
        self._export_usd(_file_path, _start, _end)