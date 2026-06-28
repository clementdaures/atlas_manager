"""Ingest Alembic Bundle."""

from pathlib import Path
import re
import hou
from atlas_manager.dcc.ingest_core import IngestCore


class AlembicBundled(IngestCore):
    """Ingest Alembic Bundle - imports multiple alembics from a bundle folder into stage context."""

    nice_name = "Ingest Alembic Bundle to obj"
    valid_extensions = [".abc"]  # Set to .abc to match bundle contents
    referencable = True
    bundled = True
    bundle_match_id = 8001  # Shared ID across Maya and Houdini for cross-DCC compatibility

    def __init__(self):
        super(AlembicBundled, self).__init__()

        # Define category-specific import methods if needed
        self.category_functions = {
            "Model": self._bring_in_model,
            "Animation": self._bring_in_animation,
            "Fx": self._bring_in_fx,
            "Layout": self._bring_in_layout,
            "Lighting": self._bring_in_lighting,
        }

    def _parse_filename(self):
        """Parse the filename to extract task name and category.
        Expected format: pro_<task>_<category>.abc
        Example: pro_rani_mdl.abc -> task: rani, category: mdl
        """
        file_path = Path(self.ingest_path)
        filename = file_path.stem  # Get filename without extension

        # Split by underscore
        parts = filename.split("_")

        if len(parts) >= 3:
            # Format: pro_<task>_<category>
            publish_type = parts[0]

            task_list = parts[1:-1]
            underscore = "_"
            task_name = underscore.join(task_list)

            category_code = parts[2]
            return publish_type, task_name, category_code
        else:
            # Fallback to filename
            return "pbh", filename, "default"

    @staticmethod
    def sanitize_node_path(path):
        """Sanitize a string to be a valid Houdini node name."""
        sanitized_path = re.sub(r"\\", "/", str(path))
        return sanitized_path

    def _create_sublayer_in_stage(self):
        """Create or update sublayer in stage context based on filename nomenclature."""
        # Get the project path
        project_path = hou.getenv("JOB")
        # Try to get a relative path to the project. If not possible, use absolute path.
        try:
            _file_path = Path("$JOB") / Path(self.ingest_path).relative_to(project_path)
        except (ValueError, TypeError):
            _file_path = Path(self.ingest_path)

        sanitized_path = self.sanitize_node_path(_file_path)

        # Parse filename to get task and category
        publish_type, task_name, category_code = self._parse_filename()

        # Get stage context
        node = hou.node("obj")

        # Check if subnet with task name exists
        geo_name = f"{task_name}"
        geo_node = node.node(geo_name)

        if geo_node is None:
            # Create subnet for this task
            geo_node = node.createNode("geo", node_name=geo_name)
            print(f"Created subnet: {geo_node}")

        geo_node.moveToGoodPosition()

        # Navigate into the subnet and create/update sublayer
        alembic_name = f"{_file_path.stem}"
        alembic_sop = geo_node.node(alembic_name)

        if alembic_sop:
            # Sublayer exists, update the file path
            print(f"Updating existing sop: {alembic_sop}")
            alembic_sop.moveToGoodPosition()
            alembic_sop.parm("fileName").set(str(sanitized_path))
        else:
            # create alembic SOP inside geo node
            alembic_sop = geo_node.createNode("alembic", node_name=_file_path.stem)
            alembic_sop.moveToGoodPosition()
            alembic_sop.parm("fileName").set(str(sanitized_path))

            print(f"Created sublayer: {alembic_sop} with file: {sanitized_path}")

        # Set display flag on the sublayer
        alembic_sop.setDisplayFlag(True)

        return alembic_sop

    def _bring_in_model(self):
        """Import Alembic File for Model category."""
        print(f"Bringing in Alembic Bundle - Model: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _bring_in_animation(self):
        """Import Alembic File for Animation category."""
        print(f"Bringing in Alembic Bundle - Animation: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _bring_in_fx(self):
        """Import Alembic File for FX category."""
        print(f"Bringing in Alembic Bundle - FX: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _bring_in_layout(self):
        """Import Alembic File for Layout category."""
        print(f"Bringing in Alembic Bundle - Layout: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _bring_in_lighting(self):
        """Import Alembic File for Lighting category."""
        print(f"Bringing in Alembic Bundle - Lighting: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _bring_in_default(self):
        """Import Alembic File with default settings.
        This should not be called if category_functions are properly defined.
        """
        print(f"Bringing in Alembic Bundle - Default: {self.ingest_path}")
        return self._create_sublayer_in_stage()

    def _reference_default(self):
        """Reference Alembic File."""
        # Identical to bring in for stage context
        return self._create_sublayer_in_stage()