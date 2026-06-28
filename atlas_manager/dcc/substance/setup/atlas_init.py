# Atlas Manager [Start]
import sys

atlas_path = 'D:\\andhakara\\'
if not atlas_path in sys.path:
    sys.path.append(atlas_path)
# Atlas Manager [End]

from atlas_manager.ui.Qt import QtWidgets
import substance_painter.ui
from atlas_manager.ui import main
from atlas_manager.plugins.trolling import ee_substance as easter

plugin_widgets = []


def __main_ui():
    """Launch main ui."""
    tui = main.launch(dcc="Substance")
    # plugin_widgets.append(tui)


def __new_version():
    """New version."""
    tui = main.launch("Substance", dont_show=True)
    # plugin_widgets.append(tui)
    tui.on_new_version()


def __publish():
    """New version."""
    tui = main.launch("Substance", dont_show=True)
    # plugin_widgets.append(tui)
    tui.on_publish_scene()


def start_plugin():
    # Get the application main window.
    easter.show_gif_window()

    mainWindow = substance_painter.ui.get_main_window()
    plugin_widgets.append(mainWindow)

    atlas_manager_menu = mainWindow.menuBar().addMenu("Atlas Manager")
    plugin_widgets.append(atlas_manager_menu)

    main_ui_action = QtWidgets.QAction("Main UI")
    plugin_widgets.append(main_ui_action)
    atlas_manager_menu.addAction(main_ui_action)

    new_version_action = atlas_manager_menu.addAction("New Version")
    plugin_widgets.append(new_version_action)

    publish_action = atlas_manager_menu.addAction("Publish")
    plugin_widgets.append(publish_action)

    # SIGNALS
    main_ui_action.triggered.connect(__main_ui)
    new_version_action.triggered.connect(__new_version)
    publish_action.triggered.connect(__publish)


def close_plugin():
    # Remove all atlas manager widgets that are lingering around.
    for widget in QtWidgets.QApplication.topLevelWidgets():
        # for widget in QtWidgets.QApplication.allWidgets():
        if widget.__module__.startswith("atlas_manager."):
            substance_painter.ui.delete_ui_element(widget)


if __name__ == "__main__":
    start_plugin()