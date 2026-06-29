"""UI Extension for Ftrack"""
import webbrowser
import os
# Uncomment following if dotenv installed
# from dotenv import load_dotenv

from atlas_manager.ui.Qt import QtWidgets
from atlas_manager.ui.dialog.feedback import Feedback
from atlas_manager.management.extension_core import ExtensionCore

class UiExtensions(ExtensionCore):
    def __init__(self, parent):
        self.parent = parent
        self.feedback = Feedback(parent=self.parent)

    def build_ui(self):
        """Build the extension UI."""
        self.add_main_menu()

    def add_main_menu(self):
        """Add the extension commands to the main menu."""
        ftrack_menu = self.parent.menu_bar.addMenu("Ftrack")

        open_ftrack = QtWidgets.QAction("Open &Ftrack", self.parent)
        ftrack_menu.addAction(open_ftrack)

        # SIGNALS
        open_ftrack.triggered.connect(self.on_open_ftrack)

    @staticmethod
    def on_open_ftrack():
        """Open Ftrack website."""
        # Uncomment following if dotenv installed
        # load_dotenv()

        url = os.environ.get("FTRACK_LINK") or "your_ftrack_website_pass_here"

        # Open in default browser
        webbrowser.open(url)