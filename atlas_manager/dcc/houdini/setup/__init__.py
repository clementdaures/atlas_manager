from pathlib import Path
import hou

# current location
self_location = Path(__file__).parent
icons_folder = self_location / "icons"

try:
    atlas_manager_shelf = hou.shelves.shelves()["AtlasManager"]
except KeyError:
    atlas_manager_shelf = hou.shelves.newShelf(name="Atlas Manager", label="AtlasManager")

atlas_manager_shelf.setTools([])

tools = []


main_ui_command = """
from atlas_manager.ui import main as atlas_main
atlas_main.launch(dcc="Houdini")
"""
main_ui_icon = str(icons_folder / "atlas_main_ui.png")
main_ui_tool = hou.shelves.newTool(name="MainUI", label="MainUI", script=main_ui_command, icon=main_ui_icon)
tools.append(main_ui_tool)


new_version_command = """
from atlas_manager.ui import main as atlas_main
tui = atlas_main.launch(dcc='Houdini', dont_show=True)
tui.on_new_version()
"""
new_version_icon = str(icons_folder / "atlas_new_version.png")
new_version_tool = hou.shelves.newTool(name="NewVersion", label="New Version", script=new_version_command, icon=new_version_icon)
tools.append(new_version_tool)


publish_scene_command = """
from atlas_manager.ui import main as atlas_main
tui = atlas_main.launch(dcc='Houdini', dont_show=True)
tui.on_publish_scene()
"""
publish_scene_icon = str(icons_folder / "atlas_publish.png")
publish_scene_tool = hou.shelves.newTool(name="PublishScene", label="Publish Scene", script=publish_scene_command, icon=publish_scene_icon)
tools.append(publish_scene_tool)


import_separator_icon = str(icons_folder / "atlas_separator.png")
import_separator_tool = hou.shelves.newTool(name="Separator", label="Separator", script=None, icon=import_separator_icon)
tools.append(import_separator_tool)


import_chr_lookdev_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_chr_ldv()
"""
import_chr_lookdev_icon = str(icons_folder / "atlas_asset_ldv.png")
import_chr_lookdev_tool = hou.shelves.newTool(name="ImportLookdev", label="Import Lookdev", script=import_chr_lookdev_command, icon=import_chr_lookdev_icon)
tools.append(import_chr_lookdev_tool)


import_reset_command = """
from atlas_manager.plugins import reset_mplay
reset_mplay.reset_ipr()
"""
import_reset_icon = str(icons_folder / "atlas_ipr_reset.png")
import_reset_tool = hou.shelves.newTool(name="ResetIPR", label="Reset IPR", script=import_reset_command, icon=import_reset_icon)
tools.append(import_reset_tool)


import_parse_command = """
from atlas_manager.plugins import parse_tex
parse_tex.parse_and_rename()
"""
import_parse_icon = str(icons_folder / "atlas_parse_tex.png")
import_parse_tool = hou.shelves.newTool(name="ParseTexture", label="Parse Texture", script=import_parse_command, icon=import_parse_icon)
tools.append(import_parse_tool)


render_lookdev_command = """
from atlas_manager.plugins import export_render as exp_rdr
exp_rdr.render_lookdev()
"""
render_lookdev_icon = str(icons_folder / "atlas_asset_rdr.png")
render_lookdev_tool = hou.shelves.newTool(name="AssetRender", label="Asset Render", script=render_lookdev_command, icon=render_lookdev_icon)
tools.append(render_lookdev_tool)


import_separator_icon = str(icons_folder / "atlas_separator.png")
import_separator_tool = hou.shelves.newTool(name="Separator", label="Separator", script=None, icon=import_separator_icon)
tools.append(import_separator_tool)


import_asset_asb_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_asset_asb()
"""

import_asset_asb_icon = str(icons_folder / "atlas_asset_asb.png")
import_asset_asb_tool = hou.shelves.newTool(name="ImportAsbChara", label="Import Asset Asb", script=import_asset_asb_command, icon=import_asset_asb_icon)
tools.append(import_asset_asb_tool)


import_shot_asb_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_shot_asb()
"""

import_shot_asb_icon = str(icons_folder / "atlas_shot_asb.png")
import_shot_asb_tool = hou.shelves.newTool(name="ImportAsbSet", label="Import Shot Asb", script=import_shot_asb_command, icon=import_shot_asb_icon)
tools.append(import_shot_asb_tool)


import_separator_icon = str(icons_folder / "atlas_separator.png")
import_separator_tool = hou.shelves.newTool(name="Separator", label="Separator", script=None, icon=import_separator_icon)
tools.append(import_separator_tool)


import_shot_light_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_shot_light()
"""

import_shot_light_icon = str(icons_folder / "atlas_shot_light.png")
import_shot_light_tool = hou.shelves.newTool(name="ImportLighting", label="Import Shot Light", script=import_shot_light_command, icon=import_shot_light_icon)
tools.append(import_shot_light_tool)


assign_shots_command = """
from atlas_manager.plugins.lighting import show_assignment_panel
show_assignment_panel()
"""

assign_shots_icon = str(icons_folder / "atlas_assign_light.png")
assign_shots_tool = hou.shelves.newTool(name="AssignShot", label="Assign Shot", script=assign_shots_command, icon=assign_shots_icon)
tools.append(assign_shots_tool)


select_shot_command = """
from atlas_manager.plugins.lighting import show_selection_panel
show_selection_panel()
"""

select_shot_icon = str(icons_folder / "atlas_select_light.png")
select_shot_tool = hou.shelves.newTool(name="SelectShot", label="Select Shot", script=select_shot_command, icon=select_shot_icon)
tools.append(select_shot_tool)


write_shot_command = """
from atlas_manager.plugins.lighting import show_write_panel
show_write_panel()
"""

write_shot_icon = str(icons_folder / "atlas_shot_rdr.png")
write_shot_tool = hou.shelves.newTool(name="ShotWriter", label="Shot Writer", script=write_shot_command, icon=write_shot_icon)
tools.append(write_shot_tool)


import_separator_icon = str(icons_folder / "atlas_separator.png")
import_separator_tool = hou.shelves.newTool(name="Separator", label="Separator", script=None, icon=import_separator_icon)
tools.append(import_separator_tool)


import_groom_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_shot_groom()
"""

import_groom_icon = str(icons_folder / "atlas_shot_groom.png")
import_groom_tool = hou.shelves.newTool(name="ImportGroom", label="Import Shot Groom", script=import_groom_command, icon=import_groom_icon)
tools.append(import_groom_tool)


import_shot_cloth_command = """
from atlas_manager.plugins import import_template as imp_templ
imp_templ.import_shot_cloth()
"""

import_shot_cloth_icon = str(icons_folder / "atlas_shot_cloth.png")
import_shot_cloth_tool = hou.shelves.newTool(name="ImportCloth", label="Import Shot Cloth", script=import_shot_cloth_command, icon=import_shot_cloth_icon)
tools.append(import_shot_cloth_tool)


import_separator_icon = str(icons_folder / "atlas_separator.png")
import_separator_tool = hou.shelves.newTool(name="Separator", label="Separator", script=None, icon=import_separator_icon)
tools.append(import_separator_tool)


import_autofill_command = """
from atlas_manager.plugins import shot_filler
shot_filler.auto_fill_sequence_shot()
"""
import_autofill_icon = str(icons_folder / "atlas_autofill_shot.png")
import_autofill_tool = hou.shelves.newTool(name="ParseShot", label="Parse Shot", script=import_autofill_command, icon=import_autofill_icon)
tools.append(import_autofill_tool)


atlas_manager_shelf.setTools(tools)