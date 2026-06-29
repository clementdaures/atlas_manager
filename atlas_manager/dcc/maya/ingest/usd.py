"""Ingest USD."""

from pathlib import Path

import logging

from maya import cmds
from maya import OpenMaya as om
from atlas_manager.dcc.ingest_core import IngestCore

LOG = logging.getLogger(__name__)

class USD(IngestCore):
    """Ingest USD."""

    nice_name =  "Ingest USD"
    valid_extensions = [".usd", ".usda", ".usdc"]
    referencable = True

    def __init__(self):
        super(USD, self).__init__()
        if not cmds.pluginInfo("mayaUsdPlugin", loaded=True, query=True):
            try:
                cmds.loadPlugin("mayaUsdPlugin")
            except Exception as exc:
                om.MGlobal.displayInfo("mayaUsdPlugin cannot be initialized")
                raise exc

        self.category_functions = {"Model": self._bring_in_model,
                                   "LookDev": self._bring_in_lookdev,
                                   "Assembly": self._bring_in_assembly,
                                   "Layout": self._bring_in_layout,
                                   "Animation": self._bring_in_animation,
                                   "Fx": self._bring_in_fx,
                                   "Lighting": self._bring_in_lighting,
                                   }

    def _bring_in_default(self):
        """Import USD File with default settings."""
        cmds.mayaUSDImport(file=self.ingest_path, primPath="/")


    def _reference_default(self):
        """Reference USD File with default settings."""

        # this method will be used for all categories
        namespace = self.namespace or Path(self.ingest_path).stem
        ref = cmds.file(
            self.ingest_path,
            reference=True,
            groupLocator=True,
            mergeNamespacesOnClash=False,
            namespace=namespace,
            returnNewNodes=True,
        )
        return ref
