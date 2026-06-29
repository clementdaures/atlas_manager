from .management_core import ManagementCore

# Dictionary to store platform classes
platforms = {}
ui_extensions = {}

from atlas_manager.management.tractor.ui_extension import UiExtensions as tractor_ui_extension
ui_extensions["tractor"] = tractor_ui_extension

from atlas_manager.management.ftrack.ui_extension import UiExtensions as ftrack_ui_extension
ui_extensions["ftrack"] = ftrack_ui_extension

__all__ = ["platforms"]
