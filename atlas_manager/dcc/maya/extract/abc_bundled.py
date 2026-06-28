"""Extract Alembic references from Maya scene as a bundle"""

from maya import cmds
from maya import OpenMaya as om
from pathlib import Path

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.maya import utils


class AlembicBundled(ExtractCore):
    """Extract multiple Alembic files from Maya scene into a bundle"""

    nice_name = "Alembic Bundled"
    color = (255, 200, 100)
    bundled = True
    optional = True
    enabled = False
    bundle_match_id = 8003

    def __init__(self):
        _ranges = utils.get_ranges()

        all_refs = cmds.ls(type="reference")
        ref_items = []
        for r in all_refs:
            if r in ["sharedReferenceNode", "_UNKNOWN_REF_NODE_"]:
                continue
            try:
                ref_items.append(r)
            except Exception:
                continue

        global_exposed_settings = {
            "start_frame": {"display_name": "Start Frame", "type": "integer", "value": _ranges[0]},
            "end_frame": {"display_name": "End Frame", "type": "integer", "value": _ranges[3]},
            "sub_steps": {"display_name": "Sub Steps", "type": "integer", "value": 1},
            "references": {
                "display_name": "References to Export",
                "type": "list",
                "value": ref_items,
            },
        }

        super().__init__(global_exposed_settings=global_exposed_settings)

        if not cmds.pluginInfo("AbcExport", loaded=True, query=True):
            try:
                cmds.loadPlugin("AbcExport")
            except Exception as e:
                om.MGlobal.displayError("Alembic Export Plugin cannot be initialized")
                raise e

        self.extension = ".abc"

    # ------------------------------------------------------------------
    # Node resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _is_uppercase_node(node_short_name):
        """Return True if the bare node name (no namespace) is fully uppercase
        and contains only letters, digits, and underscores.

        Examples that pass : SOUL, UPPER, CHAR_01, WORLD
        Examples that fail : UPPER_controller, UPPER_skeleton, geometry_grp
        """
        bare = node_short_name.split(":")[-1]
        return bare == bare.upper() and bare.replace("_", "").isalnum()

    @staticmethod
    def _has_mdl_descendant(node):
        """Return True if *node* has ANY descendant transform named 'mdl'.

        Unlike the old _has_mdl_child, this walks the full subtree so that
        a high-level group like WORLD (whose mdl nodes live deeper at
        WORLD/PROP/KHUKURI/mdl) is correctly recognised as a geometry root.
        """
        descendants = cmds.listRelatives(node, allDescendents=True, type="transform", fullPath=True) or []
        for desc in descendants:
            if desc.split("|")[-1].split(":")[-1] == "mdl":
                return True
        return False

    def _find_geometry_group(self, ref):
        """Resolve the single top-level geometry group for *ref*.

        Primary  : collect all uppercase transform nodes that have an 'mdl'
                   anywhere in their subtree, then return the shallowest one
                   (fewest '|' separators in the full DAG path).
                   This guarantees WORLD is preferred over WORLD/PROP/KHUKURI,
                   and exporting it naturally includes every sibling beneath it
                   (KHUKURI, SCABBARD, etc.).
        Fallback : first transform whose short name ends with '_geometry'.

        Returns the full DAG path string, or None if nothing is found.
        """
        try:
            ref_nodes = cmds.referenceQuery(ref, nodes=True, dagPath=True)
        except Exception as e:
            om.MGlobal.displayWarning(f"Reference {ref} query failed: {e}")
            return None

        primary_matches = []
        geometry_fallback = None

        for node in ref_nodes:
            if not cmds.objExists(node):
                continue
            if cmds.nodeType(node) != "transform":
                continue

            short_name = node.split("|")[-1].split(":")[-1]

            # ── Primary rule ──────────────────────────────────────────
            if self._is_uppercase_node(short_name) and self._has_mdl_descendant(node):
                primary_matches.append(node)

            # ── Fallback candidate ────────────────────────────────────
            elif geometry_fallback is None and short_name.endswith("_geometry"):
                geometry_fallback = node

        # ── Pick the shallowest primary match ─────────────────────────
        if primary_matches:
            root = min(primary_matches, key=lambda n: n.count("|"))
            om.MGlobal.displayInfo(f"[{ref}] Primary match (shallowest UPPER+mdl descendant): {root}")
            return root

        # ── Fallback rule ─────────────────────────────────────────────
        if geometry_fallback:
            om.MGlobal.displayInfo(f"[{ref}] Fallback match (_geometry): {geometry_fallback}")
            return geometry_fallback

        om.MGlobal.displayWarning(f"[{ref}] No exportable geometry group found, skipping.")
        return None

    # ------------------------------------------------------------------
    # Output naming
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_name_for_ref(ref):
        """Use the reference's scene namespace as the output stem.

        Maya guarantees namespaces are unique per scene, so three references
        to the same pro_soul_rig.ma will produce distinct names:

            pro_soul_rig   →  pro_soul_rig.abc
            pro_soul_rig1  →  pro_soul_rig1.abc
            pro_soul_rig2  →  pro_soul_rig2.abc
        """
        try:
            namespace = cmds.referenceQuery(ref, namespace=True)
            return namespace.lstrip(":")
        except Exception:
            return ref.replace(":", "_").replace("|", "_")

    # ------------------------------------------------------------------
    # Alembic export helper
    # ------------------------------------------------------------------

    @staticmethod
    def _export_alembic_file(geometry_group, file_path, start_frame, end_frame, sub_steps):
        step = 1.0 / sub_steps if sub_steps > 1 else 1.0

        if not cmds.objExists(geometry_group):
            raise RuntimeError(f"Geometry group does not exist: {geometry_group}")

        cmds.select(geometry_group, replace=True)

        selected = cmds.ls(selection=True, long=True)
        root_flags = " ".join(f'-root "{n}"' for n in selected)

        safe_path = Path(file_path).as_posix()

        job_args = " ".join([
            f"-frameRange {start_frame} {end_frame}",
            f"-step {step}",
            "-stripNamespaces",
            "-uvWrite",
            "-writeUVSets",
            "-worldSpace",
            "-eulerFilter",
            "-wholeFrameGeo",
            "-writeVisibility",
            "-dataFormat ogawa",
            root_flags,
            f'-file "{safe_path}"',  # ← now uses forward slashes
        ])

        cmds.AbcExport(j=job_args)

    # ------------------------------------------------------------------
    # Main extraction
    # ------------------------------------------------------------------

    def _extract_default(self):
        """Bundle multiple Alembic files, one per reference."""
        _start = self.global_settings.get("start_frame")
        _end = self.global_settings.get("end_frame")
        sub_steps = self.global_settings.get("sub_steps")
        selected_refs = self.global_settings.get("references")

        bundle_dir = Path(self.resolve_output())
        bundle_dir.mkdir(parents=True, exist_ok=True)

        _bundle_info = {}

        # ── Evaluation mode ───────────────────────────────────────────
        evaluation_type = cmds.evaluationManager(query=True, mode=True)
        cmds.evaluationManager(mode="parallel")
        cmds.optionVar(intValue=("gpuOverride", 1))
        cmds.dgdirty(allPlugs=True)
        cmds.refresh(force=True)

        # ── Per-reference export ──────────────────────────────────────
        for ref in selected_refs:

            geometry_group = self._find_geometry_group(ref)
            if not geometry_group:
                continue  # warning already emitted inside helper

            safe_ref_name = self._safe_name_for_ref(ref)
            versioned_path = bundle_dir / f"{safe_ref_name}.abc"

            try:
                om.MGlobal.displayInfo(f"Exporting Alembic: {versioned_path}")
                self._export_alembic_file(
                    geometry_group,
                    versioned_path,
                    _start,
                    _end,
                    sub_steps,
                )
                om.MGlobal.displayInfo(f"Exported {safe_ref_name}: versioned={versioned_path}")

            except Exception as e:
                om.MGlobal.displayError(f"Failed to export {ref}: {e}")
                continue

            _bundle_info[ref] = {
                "extension": ".abc",
                "path": str(versioned_path),
                "sequential": False,
            }

        self.bundle_info = _bundle_info
        cmds.evaluationManager(mode=evaluation_type[0])