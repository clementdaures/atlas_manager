"""Ingest Usd."""

from pathlib import Path
import hou
from atlas_manager.dcc.ingest_core import IngestCore

import logging

LOG = logging.getLogger(__name__)


class Usd(IngestCore):
    """Ingest Usd."""

    nice_name = "USD Import"
    valid_extensions = [".usd", ".usda", ".usdc", ".usdz", ".usdnc"]
    referencable = True

    def __init__(self):
        super(Usd, self).__init__()

    def _get_project_relative_path(self):
        """Get file path relative to project, or absolute if outside project."""
        project_path = hou.getenv("JOB")
        if not project_path:
            LOG.warning("JOB environment variable not set, using absolute path")
            return Path(self.ingest_path)

        try:
            rel_path = Path(self.ingest_path).relative_to(project_path)
            return f"$JOB/{rel_path.as_posix()}"
        except ValueError:
            LOG.debug(f"Path {self.ingest_path} is outside project, using absolute path")
            return str(Path(self.ingest_path))

    def _get_current_network(self):
        """Get the current network the user is viewing."""
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if pane:
            current_node = pane.pwd()
            LOG.info(f"User is currently in: {current_node.path()}")
            return current_node
        return None

    def _is_inside_sop_context(self, node):
        """Check if a node is inside a SOP (geometry) context."""
        if node is None:
            return False
        # Check if the node's type category is SOP
        return node.type().category().name() == "Sop"

    def _find_existing_usd_import(self, node_name):
        """Find existing usdimport node, prioritizing current network."""
        # First, check current network if it's in SOP context
        current_network = self._get_current_network()
        if current_network:
            # If we're inside a geo node (SOP context)
            if self._is_inside_sop_context(current_network):
                existing = current_network.node(node_name)
                if existing and existing.type().name() == "usdimport":
                    LOG.info(f"Found existing usdimport in current location: {existing.path()}")
                    return existing
            # If we're AT a geo node (looking at it from /obj)
            elif current_network.type().name() == "geo":
                existing = current_network.node(node_name)
                if existing and existing.type().name() == "usdimport":
                    LOG.info(f"Found existing usdimport in current geo: {existing.path()}")
                    return existing

        # Then check /obj/geo
        geo = hou.node("/obj/geo")
        if geo and geo.type().name() == "geo":
            existing = geo.node(node_name)
            if existing and existing.type().name() == "usdimport":
                LOG.info(f"Found existing usdimport in /obj/geo: {existing.path()}")
                return existing

        # Finally check /obj for any geo node containing this usdimport
        obj = hou.node("/obj")
        if obj:
            for child in obj.children():
                if child.type().name() == "geo":
                    existing = child.node(node_name)
                    if existing and existing.type().name() == "usdimport":
                        LOG.info(f"Found existing usdimport in {child.path()}: {existing.path()}")
                        return existing

        return None

    def _get_or_create_geo(self, path="/obj/geo"):
        """Get or create geo node."""
        geo_node = hou.node(path)
        if geo_node is None:
            obj = hou.node("/obj")
            geo_node = obj.createNode("geo", "geo")
            # Delete default file node if it exists
            try:
                geo_node.allSubChildren()[0].destroy()
            except IndexError:
                pass
            LOG.info(f"Created geo node at {path}")
        return geo_node

    def _create_or_update_usd_import(self, parent, file_path, node_name):
        """Create or update usdimport node inside a SOP context."""
        # Check if usdimport node already exists in parent
        usd_import_node = parent.node(node_name)

        if usd_import_node and usd_import_node.type().name() == "usdimport":
            LOG.info(f"Updating existing usdimport node '{node_name}'")
        else:
            usd_import_node = parent.createNode("usdimport", node_name)
            LOG.info(f"Created usdimport node '{node_name}'")
            usd_import_node.moveToGoodPosition()

        usd_import_node.parm("filepath1").set(str(file_path))

        LOG.info(f"Set file path: {file_path}")
        return usd_import_node

    def _bring_in_default(self):
        """Import USD File in /obj using USD import node.
        This method is used for all categories where no specific method is defined.
        """
        node_name = self.namespace or Path(self.ingest_path).stem
        file_path = self._get_project_relative_path()

        # Check if usdimport node already exists somewhere
        existing_node = self._find_existing_usd_import(node_name)

        if existing_node:
            # Update existing node wherever it is
            existing_node.parm("filepath1").set(str(file_path))
            LOG.info(f"Updated existing usdimport node: {existing_node.path()}")
            return existing_node

        # Create new node in current network or fallback
        current_network = self._get_current_network()

        if current_network:
            # Check if we're inside a SOP context (subnet inside geo, etc.)
            if self._is_inside_sop_context(current_network):
                LOG.info(f"Creating usdimport in current SOP context: {current_network.path()}")
                return self._create_or_update_usd_import(current_network, file_path, node_name)
            # Check if we're AT a geo node (viewing it from /obj)
            elif current_network.type().name() == "geo":
                LOG.info(f"Creating usdimport inside geo node: {current_network.path()}")
                return self._create_or_update_usd_import(current_network, file_path, node_name)

        # Fallback to default locations
        geo = hou.node("/obj/geo")
        if geo and geo.type().name() == "geo":
            return self._create_or_update_usd_import(geo, file_path, node_name)
        else:
            LOG.warning("/obj/geo not found, creating it")
            geo = self._get_or_create_geo("/obj/geo")
            return self._create_or_update_usd_import(geo, file_path, node_name)

    def _reference_default(self):
        """Reference Usd File in /obj using USD import node."""
        self._bring_in_default()