import webbrowser
import subprocess
from pathlib import Path
import os
import time
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
        sg_menu = self.parent.menu_bar.addMenu("Tractor")

        open_tractor = QtWidgets.QAction("Open &Tractor", self.parent)
        sg_menu.addAction(open_tractor)

        open_tractor.triggered.connect(self.on_open_tractor)


    @staticmethod
    def on_open_tractor():
        """Open Tractor website."""
        # Uncomment following if dotenv installed
        # load_dotenv()

        url = os.environ.get("TRACTOR_HOST") or "your_tractor_website_pass_here"

        # Open in default browser
        webbrowser.open(url)