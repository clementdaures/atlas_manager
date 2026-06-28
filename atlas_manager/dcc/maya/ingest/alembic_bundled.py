"""Ingest Alembic Bundle."""

from pathlib import Path
from maya import cmds
from maya import OpenMaya as om
from atlas_manager.dcc.ingest_core import IngestCore


class AlembicBundled(IngestCore):
    """Ingest Alembic Bundle - imports multiple alembics from a bundle folder."""

    nice_name = "Ingest Alembic Bundle"
    valid_extensions = [".abc"]  # Set to .abc to match bundle contents
    referencable = True
    bundled = True
    bundle_match_id = 8001  # Must match the AlembicBundled extractor's ID

    def __init__(self):
        super(AlembicBundled, self).__init__()
        if not cmds.pluginInfo("AbcImport", loaded=True, query=True):
            try:
                cmds.loadPlugin("AbcImport")
            except Exception as exc:
                om.MGlobal.displayError("Alembic Import Plugin cannot be initialized")
                raise exc

        self.category_functions = {
            "Model": self._bring_in_model,
            "Animation": self._bring_in_animation,
            "Fx": self._bring_in_fx,
            "Layout": self._bring_in_layout,
            "Lighting": self._bring_in_lighting,
        }

        self.category_reference_functions = {
            "Model": self._reference_default,
            "Animation": self._reference_default,
            "Fx": self._reference_default,
            "Layout": self._reference_default,
            "Lighting": self._reference_default,
        }

    def _bring_in_model(self):
        """Import Alembic file."""
        om.MGlobal.displayInfo(f"Bringing in Alembic Bundle Item - Model: {self.ingest_path}")
        try:
            cmds.AbcImport(self.ingest_path, mode="import", fitTimeRange=False, setToStartFrame=False)
            om.MGlobal.displayInfo(f"Successfully imported: {self.ingest_path}")
        except Exception as e:
            om.MGlobal.displayError(f"Failed to import {self.ingest_path}: {e}")
            import traceback
            om.MGlobal.displayError(traceback.format_exc())
            raise

    def _bring_in_animation(self):
        """Import Alembic file with animation settings."""
        om.MGlobal.displayInfo(f"Bringing in Alembic Bundle Item - Animation: {self.ingest_path}")
        try:
            cmds.AbcImport(self.ingest_path, mode="import", fitTimeRange=True, setToStartFrame=True)
            om.MGlobal.displayInfo(f"Successfully imported: {self.ingest_path}")
        except Exception as e:
            om.MGlobal.displayError(f"Failed to import {self.ingest_path}: {e}")
            import traceback
            om.MGlobal.displayError(traceback.format_exc())
            raise

    def _bring_in_fx(self):
        """Import Alembic file - FX."""
        om.MGlobal.displayInfo("Bringing in Alembic Bundle Item - FX")
        return self._bring_in_animation()

    def _bring_in_layout(self):
        """Import Alembic file - Layout."""
        om.MGlobal.displayInfo("Bringing in Alembic Bundle Item - Layout")
        return self._bring_in_animation()

    def _bring_in_lighting(self):
        """Import Alembic file - Lighting."""
        om.MGlobal.displayInfo("Bringing in Alembic Bundle Item - Lighting")
        return self._bring_in_animation()

    def _bring_in_default(self):
        """Import Alembic file with default settings."""
        om.MGlobal.displayInfo(f"Bringing in Alembic Bundle Item with default settings: {self.ingest_path}")
        try:
            cmds.AbcImport(self.ingest_path)
            om.MGlobal.displayInfo(f"Successfully imported: {self.ingest_path}")
        except Exception as e:
            om.MGlobal.displayError(f"Failed to import {self.ingest_path}: {e}")
            import traceback
            om.MGlobal.displayError(traceback.format_exc())
            raise

    def _reference_default(self):
        """Create GPU Cache node for the alembic."""
        om.MGlobal.displayInfo(f"Creating GPU Cache reference for: {self.ingest_path}")

        # Create Cache Node
        nicename = self.namespace or Path(self.ingest_path).stem
        counter = 1
        while cmds.namespace(exists=f"{nicename}_{str(counter).zfill(3)}"):
            counter += 1
        namespace = f"{nicename}_{str(counter).zfill(3)}"

        cache_node = cmds.createNode("gpuCache", name=f"{nicename}Cache")
        cache_parent = cmds.listRelatives(cache_node, parent=True, path=True)
        cache_parent = cmds.rename(cache_parent, nicename)

        # Set Cache Path
        cmds.setAttr(f"{cache_node}.cacheFileName", self.ingest_path, type="string")

        # Namespace
        if not cmds.namespace(exists=namespace):
            cmds.namespace(addNamespace=namespace)

        # Apply Namespace
        cache_parent = cmds.rename(cache_parent, f"{namespace}:{cache_parent}")

        om.MGlobal.displayInfo(f"Created GPU cache: {cache_parent}")
        return cache_parent