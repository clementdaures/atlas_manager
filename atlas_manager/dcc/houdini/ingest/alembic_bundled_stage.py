"""Ingest Alembic Bundle."""

from pathlib import Path
import re
import hou
from atlas_manager.dcc.ingest_core import IngestCore


class AlembicBundled(IngestCore):
    """Ingest Alembic Bundle - imports multiple alembics from a bundle folder into stage context."""

    nice_name = "Ingest Alembic Bundle to stage"
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
    def template_task_name(root, task_name):
        """Create rename tmp in template by task name."""

        for n in root.allSubChildren():
            name = n.name()
            new_name = re.sub(r"tmp", f"{task_name}", name)
            if new_name != name:
                try:
                    n.setName(new_name, unique_name=True)
                    print(f"Renamed: {name} -> {new_name}")
                except hou.OperationFailed:
                    print(f"Could not rename {name}")

                for parm in n.parms():
                    if parm.parmTemplate().type() == hou.parmTemplateType.String:
                        val = parm.eval()
                        if isinstance(val, str) and "tmp" in val:
                            new_val = re.sub(r"tmp", task_name, val)
                            try:
                                parm.set(new_val)
                                print(f"Updated parm {parm.name()}: '{val}' -> '{new_val}'")
                            except hou.OperationFailed:
                                print(f"Could not update parm {parm.name()}")

    @staticmethod
    def sanitize_node_path(path):
        """Sanitize a string to be a valid Houdini node name."""
        sanitized_path = re.sub(r"\\", "/", str(path))
        return sanitized_path

    def _create_reference_in_stage(self):
        """Create or update reference in stage context based on filename nomenclature."""
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
        root = hou.node("/")
        self.template_task_name(root, task_name)

        for n in root.allSubChildren():
            name = n.name()
            if name == f"{task_name}_anim_LDV":
                n.moveToGoodPosition()
                n.parm("filepath1").set(str(sanitized_path))
                print("Component geometry found. The ingestion in /obj context been canceled")
                return

        # Get stage context
        stage = hou.node("/stage")
        if not stage:
            raise RuntimeError("Stage context not found at /stage")

        # Check if subnet with task name exists
        subnet_name = f"{task_name}"
        subnet = stage.node(subnet_name)

        if not subnet:
            # Create subnet for this task
            subnet = stage.createNode("subnet", node_name=subnet_name)
            subnet.moveToGoodPosition()
            print(f"Created subnet: {subnet_name}")

        # Navigate into the subnet and create/update reference
        # Sublayer name format: reference_pro_<task>_<category>
        reference_name = f"{_file_path.stem}"
        reference = subnet.node(reference_name)

        if reference:
            # Sublayer exists, update the file path
            print(f"Updating existing reference: {reference_name}")
            reference.parm("filepath1").set(str(sanitized_path))
        else:
            # Create new reference
            reference = subnet.createNode("reference", node_name=reference_name)
            reference.moveToGoodPosition()

            # Set the file path
            reference.parm("filepath1").set(str(sanitized_path))

            print(f"Created reference: {reference_name} with file: {sanitized_path}")

        # Set display flag on the reference
        reference.setDisplayFlag(True)

        return reference

    def _bring_in_model(self):
        """Import Alembic File for Model category."""
        print(f"Bringing in Alembic Bundle - Model: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _bring_in_animation(self):
        """Import Alembic File for Animation category."""
        print(f"Bringing in Alembic Bundle - Animation: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _bring_in_fx(self):
        """Import Alembic File for FX category."""
        print(f"Bringing in Alembic Bundle - FX: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _bring_in_layout(self):
        """Import Alembic File for Layout category."""
        print(f"Bringing in Alembic Bundle - Layout: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _bring_in_lighting(self):
        """Import Alembic File for Lighting category."""
        print(f"Bringing in Alembic Bundle - Lighting: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _bring_in_default(self):
        """Import Alembic File with default settings.
        This should not be called if category_functions are properly defined.
        """
        print(f"Bringing in Alembic Bundle - Default: {self.ingest_path}")
        return self._create_reference_in_stage()

    def _reference_default(self):
        """Reference Alembic File."""
        # Identical to bring in for stage context
        return self._create_reference_in_stage()