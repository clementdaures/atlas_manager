"""Run Atlas Manager Standalone edition."""

# PyInstaller "atlas_manager.py" -w -y --clean
# Move the executable and _internal folder to the root folder for the CSS to work

import sys
from atlas_manager.ui.Qt import QtWidgets
from atlas_manager.ui import main

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    atlas = main.launch()
    sys.exit(app.exec_())
