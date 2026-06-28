"""Extract USD bundle from Houdini scene"""

import logging
from pathlib import Path
import hou

from atlas_manager.dcc.extract_core import ExtractCore
from atlas_manager.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class UsdBundled(ExtractCore):
    """Extract multiple USDs from Houdini scene into a bundle"""

    nice_name = "USD Bundled"
    color = (100, 200, 255)
    bundled = True
    optional = True
    bundle_match_id = 8002  # Unique ID for USD bundler

    VALID_TYPES = {"usd_rop", "usdexport", "componentoutput"}

    def __init__(self):
        _ranges = utils.get_ranges()

        # Collect all USD export nodes from /obj and /stage contexts
        usd_nodes = set()

        # Handle /obj context - collect all valid nodes
        obj_ctx = hou.node("/obj")
        if obj_ctx:
            for node in obj_ctx.allSubChildren() + obj_ctx.children():
                if node.type().name() in self.VALID_TYPES:
                    usd_nodes.add(node)

        # Handle /stage context - only collect componentoutput nodes (skip nested rops and thumbnails)
        stage_ctx = hou.node("/stage")
        if stage_ctx:
            for node in stage_ctx.allSubChildren() + stage_ctx.children():
                if "norender" in node.name():  #Added norender
                    continue

                elif node.type().name() == "componentoutput":
                    # Check if this componentoutput is directly under /stage (not nested in another componentoutput)
                    parent = node.parent()
                    if parent and parent.path() == "/stage":
                        usd_nodes.add(node)
                    else:
                        # Check if any ancestor is a componentoutput
                        current = parent
                        is_nested = False
                        while current and current.path() != "/stage":
                            if current.type().name() == "componentoutput":
                                is_nested = True
                                break
                            current = current.parent()
                        if not is_nested:
                            usd_nodes.add(node)

                elif node.type().name() == "usd_rop":
                    # Only add usd_rop if parent is a subnet directly under /stage
                    parent = node.parent()

                    if parent:

                        if parent.path() == "/stage":
                            usd_nodes.add(node)

                        elif parent.type().name() == "subnet":
                            usd_nodes.add(node)

        usd_items = sorted(n.path() for n in usd_nodes)

        global_exposed_settings = {
            "start_frame": {
                "display_name": "Start Frame",
                "type": "integer",
                "value": _ranges[0],
            },
            "end_frame": {
                "display_name": "End Frame",
                "type": "integer",
                "value": _ranges[3],
            },
            "sub_steps": {
                "display_name": "Sub Steps",
                "type": "integer",
                "value": 1,
            },
            "usd_nodes": {
                "display_name": "USD Export Nodes to Bundle",
                "type": "list",
                "value": usd_items,
            },
        }

        super().__init__(global_exposed_settings=global_exposed_settings)

        if hou.isApprentice():
            msg = "USD export is not supported in Houdini Apprentice."
            LOG.error(msg)
            self._message = msg
            self._enabled = False
            self._state = "unavailable"

        self.extension = ".usd"

    def _get_locked_hda(self, node):
        """Find the locked HDA that contains this node."""
        current = node
        while current:
            if current.type().definition() and current.isLockedHDA():
                return current
            current = current.parent()
        return None

    def _unlock_hda_hierarchy(self, node):
        """Unlock all HDAs in the hierarchy containing this node."""
        unlocked_hdas = []
        current = node

        while current:
            if current.type().definition() and current.isLockedHDA():
                try:
                    current.allowEditingOfContents()
                    unlocked_hdas.append(current)
                    LOG.info(f"Unlocked HDA: {current.path()}")
                except Exception as e:
                    LOG.warning(f"Could not unlock HDA {current.path()}: {e}")
            current = current.parent()

        return unlocked_hdas

    def _relock_hdas(self, hda_list):
        """Re-lock a list of HDAs."""
        for hda in reversed(hda_list):  # Relock in reverse order
            try:
                hda.matchCurrentDefinition()
                LOG.info(f"Re-locked HDA: {hda.path()}")
            except Exception as e:
                LOG.warning(f"Could not re-lock HDA {hda.path()}: {e}")

    def _safe_set_parm(self, parm, value, delete_keyframes=False):
        """Safely set a parameter value with improved error handling."""
        try:
            # Delete keyframes first if requested
            if delete_keyframes:
                try:
                    parm.deleteAllKeyframes()
                except:
                    pass

            # Attempt to set the value
            parm.set(value)
            return True

        except hou.PermissionError as e:
            LOG.debug(f"Permission error setting {parm.path()}: {e}")
            return False
        except hou.OperationFailed as e:
            LOG.debug(f"Operation failed setting {parm.path()}: {e}")
            return False
        except Exception as e:
            LOG.debug(f"Error setting {parm.path()}: {e}")
            return False

    def _get_output_path_from_node(self, node):
        """Try to read the actual output path from the node."""
        try:
            # Try common output path parameters
            for parm_name in ["lopoutput", "outputfile", "file", "filename"]:
                parm = node.parm(parm_name)
                if parm:
                    return parm.eval()
        except:
            pass
        return None

    def _extract_default(self):
        """Bundle multiple USD exports from existing USD ROP/SOP nodes"""
        _start = self.global_settings.get("start_frame")
        _end = self.global_settings.get("end_frame")
        sub_steps = self.global_settings.get("sub_steps")
        selected_usd_paths = self.global_settings.get("usd_nodes")

        bundle_dir = Path(self.resolve_output())
        bundle_dir.mkdir(parents=True, exist_ok=True)
        _bundle_info = {}
        step = float(1.0 / sub_steps)

        for usd_path in selected_usd_paths:
            if any(x in usd_path.lower() for x in ["thumbnail", "preview"]):
                LOG.info(f"Skipping preview/thumbnail node {usd_path}")
                continue

            usd_node = hou.node(usd_path)
            if not usd_node:
                LOG.warning(f"USD node {usd_path} not found, skipping...")
                continue

            node_type = usd_node.type().name()
            if node_type not in self.VALID_TYPES:
                LOG.warning(f"Node {usd_path} is not a USD exporter, skipping...")
                continue

            # Unlock HDA hierarchy if needed
            unlocked_hdas = []
            if usd_node.isInsideLockedHDA():
                unlocked_hdas = self._unlock_hda_hierarchy(usd_node)
                if not unlocked_hdas:
                    LOG.warning(f"Could not unlock HDA for {usd_path}, skipping...")
                    continue

            usd_name = usd_node.name()

            safe_name = usd_name.replace(":", "_").replace("|", "_").replace("/", "_")

            # Determine file extension
            file_ext = ".usd"
            if usd_node.parm("fileformat"):
                try:
                    format_val = usd_node.parm("fileformat").eval()
                    if format_val == 0:
                        file_ext = ".usda"
                    elif format_val == 1:
                        file_ext = ".usdc"
                except:
                    pass

            _file_path = bundle_dir / f"{safe_name}{file_ext}"

            try:
                # Save original parameters
                saved_parms = {}
                parm_keys = ["lopoutput", "trange", "f1", "f2", "f3"]

                for key in parm_keys:
                    p = usd_node.parm(key)
                    if p:
                        try:
                            saved_parms[key] = p.eval()
                        except:
                            pass

                # Modify parameters
                params_set_successfully = True

                if usd_node.parm("lopoutput"):
                    if not self._safe_set_parm(usd_node.parm("lopoutput"), str(_file_path)):
                        LOG.warning(f"Could not set lopoutput for {usd_path}")
                        params_set_successfully = False

                if usd_node.parm("trange"):
                    self._safe_set_parm(usd_node.parm("trange"), 1)  # 1 = Normal (frame range)

                if usd_node.parm("f1"):
                    self._safe_set_parm(usd_node.parm("f1"), _start, delete_keyframes=True)

                if usd_node.parm("f2"):
                    self._safe_set_parm(usd_node.parm("f2"), _end, delete_keyframes=True)

                if usd_node.parm("f3"):
                    self._safe_set_parm(usd_node.parm("f3"), step)

                # If we couldn't set the output path, check where the node is actually exporting to
                if not params_set_successfully:
                    actual_output = self._get_output_path_from_node(usd_node)
                    if actual_output:
                        LOG.info(f"Using node's existing output path: {actual_output}")
                        _file_path = Path(actual_output)

                # Run export
                export_success = False

                if node_type == "usd_rop":
                    try:
                        usd_node.render()
                        export_success = True
                        LOG.info(f"Rendered USD ROP {usd_name}")
                    except Exception as e:
                        LOG.error(f"Failed to render USD ROP {usd_path}: {e}")

                elif node_type == "usdexport":
                    try:
                        usd_node.cook(force=True)

                        # Try to find and press execute button
                        execute_parm = None
                        for candidate in ["execute", "renderbutton", "save", "saverop"]:
                            execute_parm = usd_node.parm(candidate)
                            if execute_parm:
                                break

                        if execute_parm:
                            execute_parm.pressButton()
                            export_success = True
                            LOG.info(f"Exported USD SOP {usd_name} via {execute_parm.name()}")
                        else:
                            LOG.warning(f"Could not find execute button for {usd_path}")
                    except Exception as e:
                        LOG.error(f"Failed to export USD SOP {usd_path}: {e}")

                elif node_type == "componentoutput":
                    try:
                        usd_node.cook(force=True)

                        self._safe_set_parm(usd_node.parm("payloadlayer"), f"{usd_name}_payload.usdc")
                        self._safe_set_parm(usd_node.parm("geolayer"), f"{usd_name}_geo.usdc")
                        self._safe_set_parm(usd_node.parm("mtllayer"), f"{usd_name}_mtl.usdc")

                        # Try multiple export methods
                        if hasattr(usd_node, 'render'):
                            try:
                                usd_node.render()
                                export_success = True
                                LOG.info(f"Exported Component Output {usd_name} via render()")
                            except:
                                pass

                        if not export_success and usd_node.parm("execute"):
                            try:
                                usd_node.parm("execute").pressButton()
                                export_success = True
                                LOG.info(f"Exported Component Output {usd_name} via execute button")
                            except:
                                pass

                        if not export_success:
                            LOG.error(f"All export methods failed for Component Output {usd_path}")
                    except Exception as e:
                        LOG.error(f"Failed to export Component Output {usd_path}: {e}")

                # Verify export with extended wait time
                if export_success:
                    import time
                    max_wait = 5  # Increased from 2 to 5 seconds
                    wait_interval = 0.2
                    elapsed = 0

                    while not _file_path.exists() and elapsed < max_wait:
                        time.sleep(wait_interval)
                        elapsed += wait_interval

                    if _file_path.exists():
                        _bundle_info[safe_name] = {
                            "extension": file_ext,
                            "path": str(_file_path),
                            "sequential": False,
                            "source_node": usd_path,
                        }
                        LOG.info(f"Successfully added {safe_name} to bundle at {_file_path}")
                    else:
                        # Try to find the file in alternate locations
                        actual_output = self._get_output_path_from_node(usd_node)
                        if actual_output:
                            actual_path = Path(actual_output)
                            if actual_path.exists():
                                LOG.info(f"Found export at node's output path: {actual_path}")
                                _bundle_info[safe_name] = {
                                    "extension": file_ext,
                                    "path": str(actual_path),
                                    "sequential": False,
                                    "source_node": usd_path,
                                }
                            else:
                                LOG.warning(f"Export reported success but file not found at {_file_path} or {actual_path}")
                        else:
                            LOG.warning(f"Export reported success but file not found: {_file_path}")

            except Exception as e:
                LOG.error(f"Failed to export USD from {usd_path}: {e}")
                import traceback
                LOG.debug(traceback.format_exc())

            finally:
                # Restore original parameters
                '''for key, val in saved_parms.items():
                    p = usd_node.parm(key)
                    if p is not None and val is not None:
                        self._safe_set_parm(p, val)'''

                # Re-lock HDAs
                self._relock_hdas(unlocked_hdas)

        # Store bundle info
        self.bundle_info = _bundle_info

        if not _bundle_info:
            LOG.warning("No USD files were successfully exported to the bundle")
        else:
            LOG.info(f"Bundle complete with {len(_bundle_info)} USD file(s)")