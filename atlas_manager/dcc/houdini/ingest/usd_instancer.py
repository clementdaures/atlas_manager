"""Ingest Usd."""

from pathlib import Path
import hou
from atlas_manager.dcc.ingest_core import IngestCore

import logging

LOG = logging.getLogger(__name__)


class Usd(IngestCore):
    """Ingest Usd."""

    nice_name = "USD Instancer"
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

    def _is_instancer_node(self, node):
        """Check if a node is an instancer (viewed from /stage)."""
        if node is None:
            return False
        return node.type().name() == "instancer"

    def _find_existing_usd_import(self, node_name):
        """Find existing usdimport node, prioritizing current network."""
        # First, check current network if it's in SOP context (inside instancer or subnet)
        current_network = self._get_current_network()
        if current_network:
            # If we're inside SOP context (instancer's interior or subnet)
            if self._is_inside_sop_context(current_network):
                existing = current_network.node(node_name)
                if existing and existing.type().name() == "usdimport":
                    LOG.info(f"Found existing usdimport in current location: {existing.path()}")
                    return existing
            # If we're AT an instancer node (viewing it from /stage)
            elif self._is_instancer_node(current_network):
                existing = current_network.node(node_name)
                if existing and existing.type().name() == "usdimport":
                    LOG.info(f"Found existing usdimport in current instancer: {existing.path()}")
                    return existing

        # Then check /stage/instancer
        instancer = hou.node("/stage/instancer")
        if instancer and instancer.type().name() == "instancer":
            existing = instancer.node(node_name)
            if existing and existing.type().name() == "usdimport":
                LOG.info(f"Found existing usdimport in /stage/instancer: {existing.path()}")
                return existing

        # Finally check /stage for any instancer node containing this usdimport
        stage = hou.node("/stage")
        if stage:
            for child in stage.children():
                if child.type().name() == "instancer":
                    existing = child.node(node_name)
                    if existing and existing.type().name() == "usdimport":
                        LOG.info(f"Found existing usdimport in {child.path()}: {existing.path()}")
                        return existing

        return None

    def _get_or_create_instancer(self, path="/stage/instancer"):
        """Get or create instancer node."""
        instancer_node = hou.node(path)
        if instancer_node is None:
            stage = hou.node("/stage")
            if stage is None:
                stage = hou.node("/").createNode("lopnet", "stage")
                LOG.info("Created /stage LOP network")
            instancer_node = stage.createNode("instancer", "instancer")
            LOG.info(f"Created instancer node at {path}")
        return instancer_node

    def _create_or_update_usd_import(self, parent, file_path, node_name):
        """Create or update usdimport node inside an instancer (SOP context)."""
        # Check if usdimport node already exists in parent
        usd_import_node = parent.node(node_name)

        if usd_import_node and usd_import_node.type().name() == "usdimport":
            LOG.info(f"Updating existing usdimport node '{node_name}'")
        else:
            usd_import_node = parent.createNode("usdimport", node_name=node_name)
            LOG.info(f"Created usdimport node '{node_name}'")
            usd_import_node.moveToGoodPosition()

        # Set the file path
        usd_import_node.parm("filepath1").set(str(file_path))
        LOG.info(f"Set USD import file path: {file_path}")

        return usd_import_node

    def _bring_in_default(self):
        """Import USD File in /stage/instancer using usdimport node.
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
            # Check if we're inside a SOP context (instancer's interior or subnet inside instancer)
            if self._is_inside_sop_context(current_network):
                LOG.info(f"Creating usdimport in current SOP context: {current_network.path()}")
                return self._create_or_update_usd_import(current_network, file_path, node_name)
            # Check if we're AT an instancer node (viewing it from /stage)
            elif self._is_instancer_node(current_network):
                LOG.info(f"Creating usdimport inside instancer node: {current_network.path()}")
                return self._create_or_update_usd_import(current_network, file_path, node_name)

        # Fallback to default locations
        instancer = hou.node("/stage/instancer")
        if instancer and instancer.type().name() == "instancer":
            return self._create_or_update_usd_import(instancer, file_path, node_name)
        else:
            LOG.warning("/stage/instancer not found, creating it")
            instancer = self._get_or_create_instancer("/stage/instancer")
            return self._create_or_update_usd_import(instancer, file_path, node_name)

    def _reference_default(self):
        """Reference Usd File in /stage/instancer using usdimport node."""
        self._bring_in_default()