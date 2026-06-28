# pylint: disable=too-many-locals, line-too-long, too-many-statements

"""Convenience functions for installing and integrating DCCs."""
import getopt
import logging
import os
import platform
import shutil
import sys
import winreg as reg
from pathlib import Path

import psutil

if platform.system() != "Windows":
    raise OSError("This module currently only works on Windows")

from atlas_manager import _version
from atlas_manager.core import utils


LOG = logging.getLogger(__name__)

FROZEN = getattr(sys, "frozen", False)


def print_msg(msg):
    """Prints a message to the console."""
    sys.stdout.write(f"{msg}\n")


class Installer:
    """A simple command line interface for installing software."""

    def __init__(self, argv):
        self.argv = argv

        # variables
        self.user_home = Path(utils.get_home_dir())
        self.user_documents = self.user_home / "Documents"
        self.atlas_local = self.user_home / "AtlasManager"
        self.atlas_local.mkdir(exist_ok=True)

        if FROZEN:
            self.atlas_root = Path(sys.executable).parent.parent.parent
        else:
            self.atlas_root = Path(__file__).parent.parent

        self.atlas_dcc_folder = self.atlas_root / "dcc"

        # when changing the mapping, the install all function should be updated
        # Any changes here also needs to be reflected to the package/release_package.py
        # and packacge/atlas_manager_innosetup.iss
        self.dcc_mapping = {
            "Maya": self.maya_setup,
            "Houdini": self.houdini_setup,
            "Nuke": self.nuke_setup,
            "Mari": self.mari_setup,
            "Substance": self.substance_setup,
        }

    def install_all(self):
        """Installs all the plugins."""
        self.maya_setup(prompt=False)
        self.houdini_setup(prompt=False)
        self.nuke_setup(prompt=False)
        self.mari_setup(prompt=False)
        self.substance_setup(prompt=False)
        ret = input("Setup Completed. Press Enter to Exit...")
        assert isinstance(ret, str)
        sys.exit()

    def maya_setup(self, prompt=True):
        """Installs the Maya plugin."""
        print_msg("\n")
        print_msg("**********************")
        print_msg("Starting Maya Setup...")
        print_msg("**********************")

        if self.check_running_instances("maya") == -1:
            print_msg("Installation aborted by user.")
            return

        user_maya_folder = self.user_documents / "maya"

        if not user_maya_folder.exists():
            print_msg("No Maya version can be found in the user's documents directory")
            print_msg(
                "Make sure Maya is installed and try again. "
                "Alternatively you can try manual install. "
                "Check the documentation for more information."
            )
            if prompt:
                _r = input("Press Enter to continue...")
                assert isinstance(_r, str)
            return

        modules_folder = user_maya_folder / "modules"
        modules_folder.mkdir(parents=True, exist_ok=True)
        atlas_manager_module = (
            self.atlas_dcc_folder / "maya" / "setup" / "atlas_manager_module"
        )

        module_file = modules_folder / "atlas_manager.mod"
        module_content = f"+ atlas_manager 4.0.1 {atlas_manager_module.as_posix()}"
        injector = Injector(module_file)
        injector.replace_all(module_content)

        print_msg("Maya setup completed.")
        if prompt:
            _r = input("Press Enter to continue...")
            assert isinstance(_r, str)

    def houdini_setup(self, prompt=True):
        """Installs the Houdini plugin."""
        print_msg("\n")
        print_msg("*************************")
        print_msg("Starting Houdini Setup...")
        print_msg("*************************")

        if self.check_running_instances("houdini") == -1:
            print_msg("Installation aborted by user.")
            return

        print_msg("Finding Houdini Versions...")

        # find all folders under user documents folder that start with "houdini"
        houdini_folders = [
            x
            for x in self.user_documents.iterdir()
            if x.is_dir() and x.name.startswith("houdini")
        ]

        if houdini_folders:
            print_msg("Houdini versions found:")
            for folder in houdini_folders:
                print_msg(f"{folder.name}")
        else:
            if prompt:
                print_msg(
                    "No Houdini version can be found in the user's documents directory."
                )
                print_msg(
                    "Make sure Houdini is installed and try again. Alternatively you can try manual install. "
                    "Check the documentation for more information."
                )
                if prompt:
                    _r = input("Press Enter to continue...")
                    assert isinstance(_r, str)
            return

        main_ui_icon = (
            self.atlas_dcc_folder / "houdini" / "setup" / "icons" / "atlas_main_ui.png"
        )
        new_version_icon = (
            self.atlas_dcc_folder / "houdini" / "setup" / "icons" / "atlas_new_version.png"
        )
        publish_icon = (
            self.atlas_dcc_folder / "houdini" / "setup" / "icons" / "atlas_publish.png"
        )

        script456_content = [
            "# Atlas Manager [Start]\n",
            "import sys\n",
            f"atlas_path = '{self.atlas_root.parent.as_posix()}'\n",
            "if not atlas_path in sys.path:\n",
            "    sys.path.append(atlas_path)\n",
            "# Atlas Manager [End]\n",
        ]

        shelf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <!-- This file contains definitions of shelves, toolbars, and tools.
 It should not be hand-edited when it is being used by the application.
 Note, that two definitions of the same element are not allowed in
 a single file. -->

  <toolshelf name="AtlasManager" label="AtlasManager">
    <memberTool name="MainUI"/>
    <memberTool name="NewVersion"/>
    <memberTool name="PublishScene"/>
  </toolshelf>

  <tool name="MainUI" label="MainUI" icon="{main_ui_icon.as_posix()}">
    <script scriptType="python"><![CDATA[
from atlas_manager.ui import main as atlas_main
atlas_main.launch(dcc="Houdini")
]]></script>
  </tool>

  <tool name="NewVersion" label="NewVersion" icon="{new_version_icon.as_posix()}">
    <script scriptType="python"><![CDATA[
from atlas_manager.ui import main as atlas_main
tui = atlas_main.launch(dcc='Houdini', dont_show=True)
tui.on_new_version()
]]></script>
  </tool>

  <tool name="PublishScene" label="PublishScene" icon="{publish_icon.as_posix()}">
    <script scriptType="python"><![CDATA[
from atlas_manager.ui import main as atlas_main
tui = atlas_main.launch(dcc='Houdini', dont_show=True)
tui.on_publish_scene()
]]></script>
  </tool>
</shelfDocument>
"""
        for version in houdini_folders:
            print_msg(f"Setting up {version.name}...")
            scripts_folder = version / "scripts"
            scripts_folder.mkdir(parents=True, exist_ok=True)
            script456_file = scripts_folder / "456.py"
            print_msg("Path configuration added to 456.py")

            injector = Injector(script456_file)
            injector.inject_between(
                script456_content,
                start_line="# Atlas Manager [Start]\n",
                end_line="# Atlas Manager [End]\n",
            )

            shelf_folder = version / "toolbar"
            shelf_folder.mkdir(parents=True, exist_ok=True)
            shelf_file = shelf_folder / "atlas_manager.shelf"
            injector.set_file_path(shelf_file)
            injector.replace_all(shelf_content)
            print_msg("Shelf file created.")

        print_msg(
            "Inside Houdini, Atlas Manager shelf should be enabled "
            "for the desired shelf set by clicking to '+' "
            "icon and selecting 'shelves' sub menu."
        )

        print_msg("Houdini setup completed.")
        if prompt:
            _r = input("Press Enter to continue...")
            assert isinstance(_r, str)


    def nuke_setup(self, prompt=True):
        """Installs the Nuke plugin."""
        print_msg("\n")
        print_msg("**********************")
        print_msg("Starting Nuke Setup...")
        print_msg("**********************")

        if self.check_running_instances("Nuke") == -1:
            print_msg("Installation aborted by user.")
            return

        user_nuke_folder = self.user_home / ".nuke"

        if not user_nuke_folder.exists():
            if prompt:
                print_msg("No Nuke version can be found in the user's home directory")
                print_msg(
                    "Make sure Nuke is installed and try again. Alternatively you can try manual install. "
                    "Check the documentation for more information."
                )
                if prompt:
                    _r = input("Press Enter to continue...")
                    assert isinstance(_r, str)
            return

        init_file = user_nuke_folder / "init.py"
        menu_file = user_nuke_folder / "menu.py"

        main_ui_icon = (
            self.atlas_dcc_folder / "nuke" / "setup" / "icons" / "atlas_main_ui.png"
        )
        new_version_icon = (
            self.atlas_dcc_folder / "nuke" / "setup" / "icons" / "atlas_new_version.png"
        )
        publish_icon = (
            self.atlas_dcc_folder / "nuke" / "setup" / "icons" / "atlas_publish.png"
        )

        shutil.copyfile(main_ui_icon, user_nuke_folder / "atlas_main_ui.png")
        shutil.copyfile(new_version_icon, user_nuke_folder / "atlas_new_version.png")
        shutil.copyfile(publish_icon, user_nuke_folder / "atlas_publish.png")

        init_content = [
            "# Atlas Manager [Start]\n",
            "import sys\n",
            f"atlas_path = '{self.atlas_root.parent.as_posix()}'\n",
            "if not atlas_path in sys.path:\n",
            "    sys.path.append(atlas_path)\n",
            "# Atlas Manager [End]\n",
        ]

        injector = Injector(init_file)
        injector.inject_between(
            init_content,
            start_line="# Atlas Manager [Start]\n",
            end_line="# Atlas Manager [End]\n",
        )
        print_msg("init.py file updated.")

        menu_content = [
            "# Atlas Manager [Start]\n",
            "toolbar = nuke.menu('Nodes')\n",
            "smMenu = toolbar.addMenu('AtlasManager', icon='atlas_main_ui.png')\n",
            "smMenu.addCommand('Main UI', 'from atlas_manager.ui import main as atlas_main\\natlas_main.launch(dcc=\"Nuke\")', icon='atlas_main_ui.png')\n",
            "smMenu.addCommand('New Version', 'from atlas_manager.ui import main\\ntui = main.launch(dcc=\"Nuke\", dont_show=True)\\ntui.on_new_version()', icon='atlas_new_version.png')\n",
            "smMenu.addCommand('Publish', 'from atlas_manager.ui import main\\ntui = main.launch(dcc=\"Nuke\", dont_show=True)\\ntui.on_publish_scene()', icon='projectMaterials_ICON.png')\n",
            "# Atlas Manager [End]\n",
        ]

        injector.set_file_path(menu_file)
        injector.inject_between(
            menu_content,
            start_line="# Atlas Manager [Start]\n",
            end_line="# Atlas Manager [End]\n",
        )
        print_msg("menu.py file updated.")

        print_msg("Nuke setup completed.")
        if prompt:
            _r = input("Press Enter to continue...")
            assert isinstance(_r, str)


    def mari_setup(self, prompt=True):
        """Install Mari."""
        print_msg("\n")
        print_msg("**********************")
        print_msg("Starting Mari Setup...")
        print_msg("**********************")

        if self.check_running_instances("Mari") == -1:
            print_msg("Installation aborted by user.")
            return

        mari_folder = self.user_home / "Documents" / "Mari"
        if not mari_folder.exists():
            print_msg("No Mari version can be found in the user's documents directory.")
            print_msg(
                "Make sure Mari is installed and try again. "
                "Alternatively you can try manual install. "
                "Check the documentation for more information."
            )
            if prompt:
                ret = input("Press Enter to continue...")
                assert isinstance(ret, str)
            return

        user_mari_scripts_folder = mari_folder / "Scripts"
        user_mari_scripts_folder.mkdir(parents=True, exist_ok=True)

        source_script = self.atlas_dcc_folder / "mari" / "setup" / "atlasmanager_init.py"

        # copy the source to the user's scripts folder
        init_file = user_mari_scripts_folder / "atlasmanager_init.py"
        shutil.copy(source_script, init_file)

        injector = Injector(init_file)
        injector.match_mode = "contains"
        injector.replace_single_line(
            f"atlas_path = '{self.atlas_root.parent.as_posix()}'", line="atlas_path = "
        )

        print_msg("Mari setup completed.")
        if prompt:
            _r = input("Press Enter to continue...")
            assert isinstance(_r, str)


    def substance_setup(self, prompt=True):
        """Install Substance integration."""
        print_msg("\n")
        print_msg("**************************************")
        print_msg("Starting Substance 3d Painter Setup...")
        print_msg("**************************************")

        # find the substance installation folder.
        substance_startup_folder = (
            self.user_home
            / "Documents"
            / "Adobe"
            / "Adobe Substance 3D Painter"
            / "python"
            / "startup"
        )

        if not substance_startup_folder.exists():
            print_msg(
                "No Substance version can be found. Automatic installer supports version 7.2 and above."
            )
            print_msg(
                "Make sure Substance is installed and try again. "
                "Alternatively you can try manual install. "
                "Check the documentation for more information."
            )
            if prompt:
                ret = input("Press Enter to continue...")
                assert isinstance(ret, str)
            return

        source_script = self.atlas_dcc_folder / "substance" / "setup" / "atlas_init.py"
        init_file = substance_startup_folder / "atlas_init.py"
        shutil.copy(source_script, init_file)

        injector = Injector(init_file)
        injector.match_mode = "contains"
        injector.replace_single_line(
            f"atlas_path = '{self.atlas_root.parent.as_posix()}'", line="atlas_path = "
        )

        print_msg("Substance setup completed.")
        if prompt:
            _r = input("Press Enter to continue...")
            assert isinstance(_r, str)

    def __set_csx_key(self, val):
        """Convenience function to set the csx key."""
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER,
                rf"Software\Adobe\CSXS.{val}",
                0,
                reg.KEY_ALL_ACCESS,
            )
            reg.SetValueEx(key, "PlayerDebugMode", 1, reg.REG_SZ, "1")
            reg.CloseKey(key)
            return key
        except WindowsError:
            return None

    def _ok_cancel(self, msg):
        """Displays a message box with OK and Cancel buttons."""
        reply = input(f"{msg} (y/n): ")
        assert isinstance(reply, str)
        reply = reply.lower().strip()

        if reply[0] == "y":
            return True
        if reply[0] == "n":
            return False
        return self._ok_cancel(msg)

    def _cli(self):
        """Launches a command line interface."""
        # folderCheck(network_path)
        header = f"""
-----------------------------------
Atlas Manager v{_version.__version__} - DCC Installer
-----------------------------------"""

        self.dcc_mapping.update({"Install All": self.install_all, "Exit": sys.exit})
        print_msg(header)

        while True:
            print_msg(
                """
Choose the software you want to setup Scene Manager:
----------------------------------------------------"""
            )

            # convert the self.dcc_mapping into a list of dictionaries for the menu
            menu_items = [{k: v} for k, v in self.dcc_mapping.items()]

            for item in menu_items:
                print_msg(f"[{menu_items.index(item)}] {list(item.keys())[0]}")

            choice = input(">> ")
            assert isinstance(choice, str)

            try:
                if int(choice) < 0:
                    raise ValueError
                key = list(menu_items[int(choice)])[0]
                cmd = menu_items[int(choice)][key]
                cmd()

                os.system("cls")
            except (ValueError, IndexError):
                pass

    def check_running_instances(self, instance_name):
        """Checks if the instance is running. If it is, asks the user to close it."""
        running = True
        aborted = False

        while not aborted and running:
            running = False
            for process in psutil.process_iter():
                name = str(process.name())
                if name:
                    if name.startswith(instance_name):
                        running = True
                        break

            if running:
                msg = f"{instance_name} is running. Exit software and type 'y'. type 'n' to abort"
                reply = self._ok_cancel(msg)
                if reply:
                    pass
                else:
                    aborted = True
        if aborted:
            return -1
        return 1

    def _no_cli(self, dcc_list):
        """Installs software without launching a CLI."""
        for item in dcc_list:
            func = self.dcc_mapping.get(item, None)
            if not func:
                print_msg(f"Software {item} not found in the list. Skipping...")
                continue
            func(prompt=False)
        _r = input("Setup Completed. Press Enter to Exit...")
        assert isinstance(_r, str)

    def main(self):
        """Decides to launch a CLI or proceed with installation based on arguments."""
        # parse the arguments
        opts, args = getopt.getopt(self.argv, "b", ["batchMode"])

        if not opts and not args:
            self._cli()

        elif args:
            self._no_cli(args)
        else:
            sys.exit()


class Injector:
    """Inject contents to ASCII files."""

    def __init__(self, file_path):
        self.file_path = None
        self.content = None
        self.search_list = None  # search content may be reversed or not

        self._search_direction = "forward"
        self._match_mode = "equal"
        self.force = True
        self.set_file_path(file_path)

    @property
    def search_direction(self):
        """Return defined search direction."""
        return self._search_direction

    @search_direction.setter
    def search_direction(self, value):
        """Set the search direction."""
        if value not in ["forward", "backward"]:
            raise ValueError("Invalid value")
        self._search_direction = value
        self.search_list = self.__get_search_list()

    @property
    def match_mode(self):
        """Return defined match mode."""
        return self._match_mode

    @match_mode.setter
    def match_mode(self, value):
        if value not in ["equal", "contains"]:
            raise ValueError("Invalid value")
        self._match_mode = value

    def set_file_path(self, value):
        """Sets the file path."""
        if isinstance(value, str):
            self.file_path = Path(value)
        elif isinstance(value, Path):
            self.file_path = value
        else:
            raise ValueError("Invalid value")
        self.content = self.read()
        self.search_list = self.__get_search_list()

    def __get_search_list(self):
        if self.search_direction == "forward":
            return self.content
        return self.content[::-1]

    def __add_content(self, new_content, start_idx, end_idx):
        """Adds the new content to the content list."""
        if isinstance(new_content, str):
            new_content = [new_content]
        if self.search_direction == "forward":
            added_content = (
                self.content[:start_idx] + new_content + self.content[end_idx + 1 :]
            )
        else:
            added_content = (
                self.content[:-end_idx] + new_content + self.content[-start_idx - 1 :]
            )
        return added_content

    def inject_between(
        self, new_content, start_line, end_line, suppress_warnings=False
    ):
        """Injects the new content between the start and end lines."""
        if not self.file_path.is_file():
            if self.force:
                self._dump_content(self.content)
                print_msg(f"File {self.file_path} created with new content.")
                return True
            if not suppress_warnings:
                print_msg(f"File {self.file_path} not found. Aborting.")
            return False
        start_idx, end_idx = None, None
        start_idx = self._find_index(self.search_list, start_line)
        if start_idx is not None:
            end_idx = self._find_index(self.search_list, end_line, begin_from=start_idx)
        if start_idx is None or end_idx is None:
            if self.force:
                if not suppress_warnings:
                    print_msg(
                        "Start or end line not found. Injecting at the end of the file."
                    )
                self._dump_content(self.content + new_content)
                return True
            if not suppress_warnings:
                print_msg("Start or end line not found. Aborting.")
            return False
        injected_content = self.__add_content(new_content, start_idx, end_idx)
        self._dump_content(injected_content)
        return True

    def inject_after(self, new_content, line, suppress_warnings=False):
        """Injects the new content after the line."""
        if not self.file_path.is_file():
            if self.force:
                self._dump_content(self.content)
                print_msg(f"File {self.file_path} created with new content.")
                return True
            if not suppress_warnings:
                print_msg(f"File {self.file_path} not found. Aborting.")
            return False
        start_idx = self._find_index(self.search_list, line)
        if not start_idx:
            if self.force:
                if not suppress_warnings:
                    print_msg("Line not found. Injecting at the end of the file.")
                self._dump_content(self.content + new_content)
                return True
            if not suppress_warnings:
                print_msg("Line not found. Aborting.")
            return False
        injected_content = self.__add_content(new_content, start_idx, start_idx + 1)
        self._dump_content(injected_content)
        return True

    def inject_before(self, new_content, line, suppress_warnings=False):
        """Injects the new content before the line."""
        if not self.file_path.is_file():
            if self.force:
                self._dump_content(self.content)
                print_msg(f"File {self.file_path} created with new content.")
                return True
            if not suppress_warnings:
                print_msg(f"File {self.file_path} not found. Aborting.")
            return False
        start_idx = self._find_index(self.search_list, line)
        if not start_idx:
            if self.force:
                if not suppress_warnings:
                    print_msg("Line not found. Injecting at the end of the file.")
                self._dump_content(self.content + new_content)
                return True
            if not suppress_warnings:
                print_msg("Line not found. Aborting.")
            return False
        injected_content = self.__add_content(new_content, start_idx, start_idx - 1)
        self._dump_content(injected_content)
        return True

    def replace_all(self, new_content):
        """Replace the whole file with the new content."""
        self._dump_content(new_content)
        return True

    def replace_single_line(self, new_content, line, suppress_warnings=False):
        """Replace the given line with the new content."""
        if isinstance(new_content, str):
            # if its not ending with a break line add it
            if not new_content.endswith("\n"):
                new_content = f"{new_content}\n"
            new_content = [new_content]

        if not self.file_path.is_file():
            if self.force:
                self._dump_content(self.content)
                print_msg(f"File {self.file_path} created with new content.")
                return True
            if not suppress_warnings:
                print_msg(f"File {self.file_path} not found. Aborting.")
            return False
        start_idx = self._find_index(self.search_list, line)
        if not start_idx:
            if self.force:
                if not suppress_warnings:
                    print_msg("Line not found. Injecting at the end of the file.")
                self._dump_content(self.content + new_content)
                return True
            if not suppress_warnings:
                print_msg("Line not found. Aborting.")
            return False
        injected_content = self.__add_content(new_content, start_idx, start_idx)
        self._dump_content(injected_content)
        return True

    def read(self):
        """Reads the file."""
        if not self.file_path.is_file():
            self._dump_content([])
            return []
        with open(self.file_path, "r", encoding="utf-8") as file_data:
            if file_data.mode != "r":
                return None
            content_list = file_data.readlines()
        return content_list

    def _dump_content(self, list_of_lines):
        """Write the content to the file."""
        temp_file_path = (
            self.file_path.parent / f"{self.file_path.stem}_TMP{self.file_path.suffix}"
        )
        with open(temp_file_path, "w+", encoding="utf-8") as temp_file:
            temp_file.writelines(list_of_lines)
        shutil.move(temp_file_path, self.file_path)

    def _find_index(self, search_list, line, begin_from=0):
        """Get the index of a line in a list of lines."""
        if self.match_mode == "equal" and line in search_list:
            return search_list.index(line)

        if self.match_mode == "contains":
            for idx in range(begin_from, len(search_list)):
                if line in search_list[idx]:
                    return idx
        return None


if __name__ == "__main__":
    install_handler = Installer(sys.argv[1:])
    install_handler.main()
