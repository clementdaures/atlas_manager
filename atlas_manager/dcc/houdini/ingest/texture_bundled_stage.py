"""Ingest Alembic Bundle."""

from pathlib import Path
import re
import hou
from atlas_manager.dcc.ingest_core import IngestCore


class TextureBundled(IngestCore):
    """Ingest Alembic Bundle - imports multiple alembics from a bundle folder into stage context."""

    nice_name = "Ingest Texture Bundle to stage"
    valid_extensions = [".exr", ".jpg", ".png", ".tif"]
    referencable = False
    bundled = True
    bundle_match_id = 8004


    def __init__(self):
        super(TextureBundled, self).__init__()


    def _parse_filename(self):
        """Parse the filename to extract task name and category.
        Expected format: pro_<task>_<category>.abc
        Example: pro_rani_mdl.abc -> task: rani, category: mdl
        """
        file_path = Path(self.ingest_path)
        filename = file_path.stem  # Get filename without extension

        # Split by underscore
        parts = filename.split("_")
        publish_list=["pro", "live", "pbh", "obj", "abc", "fbx"]
        map_list=["diff", "rough", "spec", "mdisp", "zdisp", "sdisp", "ccoat", "anis", "irrd", "fuzz", "sss", "sscatt", "glass", "glow", "mbump", "norm", "pres", "mask", "metal",]
        if parts[0] in publish_list:
            publish_type = parts[0]

            task_list = parts[1:-1]
            underscore = "_"
            task_name = underscore.join(task_list)

            raw_obj_name = parts[-1]
        else:
            task_list = parts[1:-1]
            underscore = "_"
            task_name = underscore.join(task_list)

            raw_obj_name = parts[-1]

        sanitized_obj_name = self._sanitize_node_name(raw_obj_name)
        sanitized_obj_parts = sanitized_obj_name.split("_")

        obj_parts = [part for part in sanitized_obj_parts if part not in map_list]
        print("obj_parts: ", obj_parts)

        if obj_parts:
            obj_name = "_".join(obj_parts)
        else:
            # Handle cases where obj_name was only a map name (e.g., 'diff')
            obj_name = ""

        return task_name, obj_name


    @staticmethod
    def _sanitize_node_name(name, lower=True):
        """Sanitize a string to be a valid Houdini node name.

        Houdini node names must:
        - Start with a letter or underscore
        - Contain only letters, numbers, and underscores
        - Not be empty
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^\w]', '_', str(name))

        if lower:
            sanitized = sanitized.lower()

        sanitized = re.sub(r'^(?:pro|live|pbh|obj|abc|fbx)_', '', sanitized)  # Remove pro/live/pbh prefix
        sanitized = re.sub(r'^(\w+)_(?:mdl|sfc|tex|anim)_', r'\1_', sanitized)  # Remove category code

        sanitized = re.sub(r'_$', r'', sanitized)

        sanitized = re.sub(r"_\d{4}", "_UDIM", sanitized)

        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized

        # Ensure it's not empty
        if not sanitized:
            sanitized = 'node'

        return sanitized

    @staticmethod
    def sanitize_node_path(path):
        """
        Sanitize a string to be a valid Houdini node name.
        Converts backslashes to forward slashes and replaces UDIM patterns.
        """
        # Convert backslashes to forward slashes
        sanitized = re.sub(r"\\", "/", str(path))

        sanitized = re.sub(r"\.\d{4}#", ".<UDIM>", sanitized)
        sanitized = re.sub(r"\.#+", ".<UDIM>", sanitized)

        sanitized = re.sub(r"\.\d{4}(?=\.)", ".<UDIM>", sanitized)

        sanitized = re.sub(r"\.\$F\d*", ".<UDIM>", sanitized)

        return sanitized

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
    def template_obj_name(root, obj_name):
        """Create rename tmp in template by obj name."""

        for n in root.allSubChildren():
            name = n.name()
            new_name = re.sub(r"objectname", f"{obj_name}", name)
            if new_name != name:
                try:
                    n.setName(new_name, unique_name=True)
                    print(f"Renamed: {name} -> {new_name}")
                except hou.OperationFailed:
                    print(f"Could not rename {name}")


    def _bring_in_default(self):
        """Create or update pxrtexture in stage context based on filename nomenclature."""
        # Get the project path
        project_path = hou.getenv("JOB")
        # Try to get a relative path to the project. If not possible, use absolute path.
        try:
            _file_path = Path("$JOB") / Path(self.ingest_path).relative_to(project_path)
        except (ValueError, TypeError):
            _file_path = Path(self.ingest_path)

        sanitized_path = self.sanitize_node_path(_file_path)

        # Parse filename to get task and category
        task_name, obj_name = self._parse_filename()

        root = hou.node("/")
        self.template_task_name(root, task_name)

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

        material_library_name = f"pro_{task_name}_tex"
        material_library = subnet.node(material_library_name)

        if material_library:
            material_library.moveToGoodPosition()
        else:
            material_library = subnet.createNode("materiallibrary", node_name=material_library_name)
            material_library.moveToGoodPosition()

        sanitized_obj = self._sanitize_node_name(obj_name, lower=False)
        self.template_obj_name(root, sanitized_obj)

        pxr_material_name = f"shd_{task_name}_{sanitized_obj}_tex"
        pxr_material = material_library.node(pxr_material_name)

        if pxr_material:
            pxr_material.moveToGoodPosition()
        else:
            pxr_material = material_library.createNode("pxrmaterialbuilder", node_name=pxr_material_name)
            pxr_material.moveToGoodPosition()

        pxr_tex_name = self._sanitize_node_name(_file_path.stem)
        pxr_tex = pxr_material.node(pxr_tex_name)

        if pxr_tex:
            # Sublayer exists, update the file path
            print(f"Updating existing reference: {material_library_name}")
            pxr_tex.parm("filename").set(str(sanitized_path))
            pxr_tex.parm("invertT").set(0)
        else:
            # Create new reference
            pxr_tex = pxr_material.createNode("pxrtexture", node_name=pxr_tex_name)

            # Set the file path
            pxr_tex.parm("filename").set(str(sanitized_path))
            pxr_tex.parm("invertT").set(0)

            print(f"Created pxr_tex: {pxr_tex_name} with file: {sanitized_path}")

        return pxr_tex