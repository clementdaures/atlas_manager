"""Ingest Alembic."""

from pathlib import Path
import re
import hou
from atlas_manager.dcc.ingest_core import IngestCore

import logging

LOG = logging.getLogger(__name__)


class Alembic(IngestCore):
    """Ingest Alembic."""

    nice_name = "Ingest Alembic"
    valid_extensions = [".abc"]
    referencable = False

    def __init__(self):
        super(Alembic, self).__init__()

    @staticmethod
    def sanitize_node_path(path):
        """Sanitize a string to be a valid Houdini node name."""
        sanitized_path = re.sub(r"\\", "/", str(path))
        return sanitized_path

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

    def _find_existing_geo_node(self, node_name):
        """Find existing geo node, prioritizing current network."""
        # First, check current network (if it's /obj or a subnet in /obj)
        current_network = self._get_current_network()
        if current_network:
            # Check if we're in /obj or a subnet within /obj
            if current_network.path().startswith("/obj"):
                existing = current_network.node(node_name)
                if existing and existing.type().name() == "geo":
                    LOG.info(f"Found existing geo node in current network: {existing.path()}")
                    return existing

        # Then check /obj directly
        obj = hou.node("/obj")
        if obj:
            existing = obj.node(node_name)
            if existing and existing.type().name() == "geo":
                LOG.info(f"Found existing geo node in /obj: {existing.path()}")
                return existing

        return None

    def _create_or_update_alembic(self, parent, file_path, node_name):
        """Create or update Alembic import inside a geo node."""
        # Check if geo node already exists
        geo_node = parent.node(node_name)

        if geo_node and geo_node.type().name() == "geo":
            LOG.info(f"Updating existing geo node '{node_name}'")
            # Find the alembic node inside
            alembic_sop = geo_node.node(node_name)
            if not alembic_sop:
                # Create alembic if it doesn't exist
                alembic_sop = geo_node.createNode("alembic", node_name=node_name)
                alembic_sop.moveToGoodPosition()
        else:
            # Create new geo node
            geo_node = parent.createNode("geo", node_name=node_name)
            LOG.info(f"Created geo node '{node_name}'")

            # Delete default file node if it exists
            try:
                geo_node.allSubChildren()[0].destroy()
            except IndexError:
                pass

            geo_node.moveToGoodPosition()

            # Create alembic node
            alembic_sop = geo_node.createNode("alembic", node_name=node_name)
            alembic_sop.moveToGoodPosition()

        # Set the file path
        sanitized_path = self.sanitize_node_path(file_path)
        alembic_sop.parm("fileName").set(str(sanitized_path))
        alembic_sop.setDisplayFlag(True)

        LOG.info(f"Set Alembic file path: {sanitized_path}")

        return geo_node, alembic_sop

    def _bring_in_default(self):
        """Import Alembic File in /obj using Alembic SOP node.
        This method is used for all categories where no specific method is defined.
        """
        node_name = Path(self.ingest_path).stem
        file_path = self._get_project_relative_path()

        # Check if node already exists
        existing_geo = self._find_existing_geo_node(node_name)

        if existing_geo:
            # Update existing node
            alembic_sop = existing_geo.node(node_name)
            if alembic_sop:
                sanitized_path = self.sanitize_node_path(file_path)
                alembic_sop.parm("fileName").set(str(sanitized_path))
                alembic_sop.setDisplayFlag(True)
                LOG.info(f"Updated existing Alembic node: {alembic_sop.path()}")
            else:
                # Create alembic inside existing geo
                alembic_sop = existing_geo.createNode("alembic", node_name=node_name)
                alembic_sop.moveToGoodPosition()
                sanitized_path = self.sanitize_node_path(file_path)
                alembic_sop.parm("fileName").set(str(sanitized_path))
                alembic_sop.setDisplayFlag(True)
                LOG.info(f"Created Alembic node in existing geo: {alembic_sop.path()}")
            return

        # Create new node in current network or /obj
        current_network = self._get_current_network()

        if current_network and current_network.path().startswith("/obj"):
            LOG.info(f"Creating Alembic in current network: {current_network.path()}")
            self._create_or_update_alembic(current_network, file_path, node_name)
        else:
            # Fallback to /obj
            obj = hou.node("/obj")
            self._create_or_update_alembic(obj, file_path, node_name)

    def _reference_default(self):
        """Reference Alembic File."""
        # identical to bring in
        self._bring_in_default()