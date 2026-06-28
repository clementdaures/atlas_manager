from maya import cmds
import atlas_manager_setup

cmds.evalDeferred(atlas_manager_setup.add_python_path)
cmds.evalDeferred(atlas_manager_setup.load_shelves)
cmds.evalDeferred(atlas_manager_setup.load_menu)
