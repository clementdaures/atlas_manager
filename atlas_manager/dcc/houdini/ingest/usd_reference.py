"""Ingest USD files into Houdini."""

from pathlib import Path
import logging
import hou
from atlas_manager.dcc.ingest_core import IngestCore

LOG = logging.getLogger(__name__)


class Usd(IngestCore):
    """Ingest USD files as references."""

    nice_name = "USD Reference"
    valid_extensions = [".usd", ".usda", ".usdc", ".usdz", ".usdnc"]
    referencable = True

    def __init__(self):
        super().__init__()

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

    def _get_or_create_lopnet(self, path="/stage"):
        """Get or create LOP network."""
        lopnet = hou.node(path)
        if lopnet is None:
            lopnet = hou.node("/").createNode("lopnet", "stage")
            LOG.info(f"Created LOP network at {path}")
        return lopnet

    def _get_current_network(self):
        """Get the current network the user is viewing."""
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if pane:
            current_node = pane.pwd()
            LOG.info(f"User is currently in: {current_node.path()}")
            return current_node
        return None

    def _find_existing_reference(self, node_name):
        """Find existing reference node, prioritizing current network."""
        # First, check current network
        current_network = self._get_current_network()
        if current_network and current_network.type().category().name() == "Lop":
            existing = current_network.node(node_name)
            if existing:
                LOG.info(f"Found existing node in current network: {existing.path()}")
                return existing

        # Then check /stage/ASSET
        asset = hou.node("/stage/ASSET")
        if asset:
            existing = asset.node(node_name)
            if existing:
                LOG.info(f"Found existing node in /stage/ASSET: {existing.path()}")
                return existing

        # Finally check /stage
        stage = hou.node("/stage")
        if stage:
            existing = stage.node(node_name)
            if existing:
                LOG.info(f"Found existing node in /stage: {existing.path()}")
                return existing

        return None

    def _create_or_update_reference(self, parent, file_path, node_name):
        """Create or update reference node."""
        # Check if node already exists in parent
        reference_node = parent.node(node_name)

        if reference_node:
            LOG.info(f"Updating existing reference node '{node_name}'")
        else:
            reference_node = parent.createNode("reference", node_name)
            LOG.info(f"Created reference node '{node_name}'")
            reference_node.moveToGoodPosition()

        reference_node.parm("filepath1").set(file_path)
        reference_node.parm("primpath1").set("/WORLD")


        LOG.info(f"Set file path: {file_path}")
        return reference_node

    def _bring_in_default(self):
        """Import USD file into current network or /stage/ASSET as fallback."""
        node_name = self.namespace or Path(self.ingest_path).stem
        file_path = self._get_project_relative_path()

        # Check if node already exists somewhere
        existing_node = self._find_existing_reference(node_name)

        if existing_node:
            # Update existing node wherever it is
            existing_node.parm("filepath1").set(file_path)
            LOG.info(f"Updated existing node: {existing_node.path()}")
            return existing_node

        # Create new node in current network or fallback
        current_network = self._get_current_network()

        if current_network and current_network.type().category().name() == "Lop":
            LOG.info(f"Creating reference in current network: {current_network.path()}")
            return self._create_or_update_reference(current_network, file_path, node_name)
        else:
            # Fallback to default locations
            asset = hou.node("/stage/ASSET")
            if asset:
                return self._create_or_update_reference(asset, file_path, node_name)
            else:
                LOG.warning("/stage/ASSET not found, using /stage")
                lopnet = self._get_or_create_lopnet("/stage")
                return self._create_or_update_reference(lopnet, file_path, node_name)

    def _reference_default(self):
        """Reference USD file as reference in /stage."""
        self._bring_in_default()