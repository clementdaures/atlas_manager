from atlas_manager.ui.widgets import path_browser
from atlas_manager.ui.widgets.common import AtlasButtonBox
from atlas_manager.ui.Qt import QtWidgets, QtCore
import atlas_manager.ui.mcv.subproject_mcv


class SubprojectBrowser(path_browser.PathBrowser):
    """A custom QLineEdit widget purposed for browsing subprojects"""

    sub = QtCore.Signal(object)

    def __init__(
        self,
        name,
        object_name=None,
        value=None,
        disables=None,
        project_object=None,
        **kwargs
    ):
        super(SubprojectBrowser, self).__init__(
            name,
            object_name=object_name,
            value=value,
            disables=disables,
            project_object=None,
            **kwargs
        )
        if not project_object:
            raise ValueError(
                "A project object must be provided to the SubprojectBrowser"
            )
        self.project_object = project_object
        self.dialog = None

    def browse(self):
        """Create a AtlasSubProject tree inside a OK - Cancel dialog
        to select the subproject
        """

        # create a dialog
        self.dialog = QtWidgets.QDialog(self)
        self.dialog.setWindowTitle("Select Subproject")
        self.dialog.setModal(True)

        # create a layout
        layout = QtWidgets.QVBoxLayout(self.dialog)
        self.dialog.setLayout(layout)

        # create a subproject tree layout
        sub_projects = atlas_manager.ui.mcv.subproject_mcv.AtlasSubProjectLayout(
            self.project_object, recursive_enabled=False, right_click_enabled=False
        )

        # get all the columns from the model and hide all of them except the first one
        columns = sub_projects.sub_view.model.columns
        sub_projects.sub_view.hide_columns(columns[1:])
        layout.addLayout(sub_projects)

        # create a button box
        button_box = AtlasButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(button_box)
        button_box.accepted.connect(self.dialog.accept)
        button_box.rejected.connect(self.dialog.reject)
        self.adjustSize()
        self.dialog.show()
        # make the dialog vertically longer but no longer than the desktop height
        self.dialog.resize(
            self.dialog.width(),
            min(
                self.dialog.height() * 2,
                QtWidgets.QApplication.desktop().height() - 100,
            ),
        )

        # move the dialog next to its parent dialog but only horizontally
        self.dialog.move(
            self.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(self.width(), 0)
        )

        # show the dialog
        if self.dialog.exec_():
            # get the model data from the selected item of AtlasProjectLayout
            _atlasSubItem = sub_projects.sub_view.get_selected_items()
            if _atlasSubItem:
                self.widget.setText(_atlasSubItem[0].subproject.path)
                self.value = _atlasSubItem[0].subproject.path
                self.com.valueChangeEvent(self.value)
                self.sub.emit(_atlasSubItem[0].subproject)
