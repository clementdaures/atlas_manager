"""Extract Alembic from Maya scene - _extra nodes and children"""

from maya import cmds
from maya import OpenMaya as om

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.maya import utils


class Alembic(ExtractCore):
    """Extract Alembic from Maya scene - _extra nodes and their children."""

    nice_name = "Alembic"
    color = (244, 132, 132)
    optional = True

    def __init__(self):
        _ranges = utils.get_ranges()
        super().__init__()
        if not cmds.pluginInfo("AbcExport", loaded=True, query=True):
            try:
                cmds.loadPlugin("AbcExport")
            except Exception as e:
                om.MGlobal.displayError("Alembic Plugin cannot be initialized")
                raise e

        om.MGlobal.displayInfo("Alembic Extractor loaded")

        self._extension = ".abc"


    def _build_root_flags(self, nodes):
        """Build -root flags for specified nodes (will include all children)."""
        return " ".join([f"-root {node}" for node in nodes])


    def _extract_default(self):
        """Extract method for any non-specified category"""
        extra_nodes = cmds.ls(selection=True)
        _file_path = self.resolve_output()
        root_flags = self._build_root_flags(extra_nodes)

        _flags = "-frameRange 0 0 -uvWrite -worldSpace -writeUVSets -writeVisibility -dataFormat ogawa"
        command = f"{_flags} {root_flags} -file {_file_path}"
        cmds.AbcExport(j=command)
        om.MGlobal.displayInfo(f"Exported _extra nodes and children to {_file_path}")