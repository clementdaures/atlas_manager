"""Main module for Mari integration."""

from pathlib import Path
import logging
# import configparser

import mari

from atlas_manager.ui.Qt import QtWidgets
from atlas_manager.dcc.main_core import MainCore
from atlas_manager.dcc.mari import validate
from atlas_manager.dcc.mari import extract
from atlas_manager.dcc.mari import ingest
from atlas_manager.dcc.mari import utils
from atlas_manager.dcc.mari import extension

LOG = logging.getLogger(__name__)


class Dcc(MainCore):
    """Mari class."""

    name = "mari"
    formats = [".mri"]  # File formats supported by the DCC
    preview_enabled = False  # Whether or not to enable the preview in the UI
    validations = validate.classes
    extracts = extract.classes
    ingests = ingest.classes
    extensions = extension.classes

    # Override the applicable methods from the MainCore class

    @staticmethod
    def pre_save_issues():
        """Checks to be done before saving a file."""
        project = mari.projects.current()
        if not project:
            return "No Mari project is open. You need to be in a project to save it."

    @staticmethod
    def get_main_window():
        """Get the main window."""
        # Set Mari main window to be in focus.
        mari.app.activateMainWindow()
        # Returns the window that has focus.
        return QtWidgets.QApplication.activeWindow()

    def save_as(self, file_path):
        """Mimic the save as functionality for Mari."""
        return utils.save_as(file_path)

    def open(self, file_path, force=True, **_extra_arguments):
        """Open the file in Mari."""
        utils.load(file_path, force)

    @staticmethod
    def is_modified():
        """Check if the scene has unsaved changes."""
        project = mari.projects.current()
        if project:
            return project.isModified()
        return False

    @staticmethod
    def get_scene_file():
        """Get the current scene file."""
        project = mari.projects.current()
        if not project:
            return ""
        project_scene_path = project.backupPath()
        # collect all the .mri files in the directory
        all_mri_files = Path(project_scene_path).glob("*.mri")
        # filter the ones that ends with _atlasmanager.mri
        atlas_files = [f for f in all_mri_files if f.stem.endswith("_atlasmanager")]
        # get the latest one
        # TODO is there a way to get the accurate one?
        if atlas_files:
            return str(atlas_files[-1])
        return ""

    def generate_thumbnail(self, file_path, width, height):
        """Generate a thumbnail for the current scene."""
        project = mari.projects.current()
        if not project:
            return None

        canvas = mari.canvases.current()
        if not canvas:
            return None

        hud_state = canvas.getDisplayProperty("HUD/RenderHud")
        if hud_state:
            canvas.setDisplayProperty("HUD/RenderHud", False)

        capt = canvas.capture(width, height)
        capt.save(file_path)

        if hud_state:
            canvas.setDisplayProperty("HUD/RenderHud", True)

        return file_path

    @staticmethod
    def get_dcc_version():
        """Get the current version of Mari."""
        version = mari.app.version()
        return str(version.major())
