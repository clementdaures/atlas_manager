"""Create a new Mari project with bundled OBJ objects."""

from pathlib import Path

import mari

from atlas_manager.dcc.ingest_core import IngestCore


class ObjBundled(IngestCore):
    """Create a new Mari project with multiple OBJ objects from a bundle."""

    nice_name = "Ingest Mari Obj (Bundled)"
    valid_extensions = [".obj"]
    bundled = True
    referencable = False
    bundle_match_id = 8003

    def _surface_path(self):
        """Return the file path."""
        file_path = Path(self.ingest_path)
        object_name = file_path.name
        root_path = file_path.parent.parent.parent.parent

        publish_type, task_name, category_code = self._parse_filename()

        return root_path / "pro" / f"pro_{task_name}_{category_code}" / object_name

    def _parse_filename(self):
        """Parse the filename to extract task name and category.
        Expected format: pro_<task>_<category>.abc
        Example: pro_rani_mdl.abc -> task: rani, category: mdl
        """
        file_path = Path(self.ingest_path)
        dir_path = file_path.parent
        dir_name = dir_path.stem

        # Split by underscore
        parts = dir_name.split("_")

        if len(parts) >= 3:
            # Format: pro_<task>_<category>
            publish_type = parts[0]
            task_name = parts[1]
            category_code = parts[2]
            return publish_type, task_name, category_code
        else:
            # Fallback to dir_name
            return "pbh", dir_name, "default"


    def _bring_in_default(self):
        """Create Mari Project with all bundled objects."""

        publish_type, task_name, category_code = self._parse_filename()
        project_name = f"{task_name}"

        # Close current project if one is open
        project_current = mari.projects.current()
        if project_current:
            if project_current.name() == project_name:
                return
            else:
                project_current.close()

        # Resolve bundle path
        bundle_path = self._surface_path()
        obj_dir = bundle_path.parent if bundle_path.is_file() else bundle_path

        # Find OBJ files
        obj_files = sorted(obj_dir.glob("*.obj"))
        if not obj_files:
            raise RuntimeError(f"No OBJ files found in {obj_dir}")

        print(f"Found {len(obj_files)} OBJ file(s) in {obj_dir}")

        # Define default channels
        channels = [
            mari.ChannelInfo("diff", 4096, 4096, mari.Image.DEPTH_HALF)
        ]

        # Metadata options
        project_meta_options = {}
        start_frame = self.metadata.get_value("start_frame", fallback_value=None)
        end_frame = self.metadata.get_value("end_frame", fallback_value=None)
        if start_frame:
            project_meta_options["StartFrame"] = start_frame
        if end_frame:
            project_meta_options["EndFrame"] = end_frame

        # Create new Mari project using the FIRST OBJ as the base geometry
        first_obj = str(obj_files[0])
        print(f"Creating new Mari project '{project_name}' from {obj_files[0].name}")

        new_project = mari.projects.create(
            project_name,
            [str(p) for p in obj_files],
            channels,
            [],
            project_meta_options
        )

        # ---------- CLEAN USELESS NODES ----------

        all_geos = mari.geo.list()

        if not all_geos:
            print(f"No geometry found in project:{project_name}")
        else:
            for geo in all_geos:
                geo_name = geo.name()
                nodegraph = geo.nodeGraph()
                all_nodes = nodegraph.nodeList()

                for node in all_nodes:
                    nodegraph.deleteNode(node)
                    print(f"Deleted node {node.name()}")

        print(f"✅ Successfully created Mari project '{project_name}' with {len(obj_files)} object(s)")
        return new_project
