# Atlas Manager [Start]
import mari
import sys
atlas_path = 'D:\\andhakara\\'
if not atlas_path in sys.path:
    sys.path.append(atlas_path)

atlas_main_ui_action = mari.actions.create('Main UI', 'from atlas_manager.ui import main;main.launch("mari")')
mari.menus.addAction(atlas_main_ui_action, 'MainWindow/Atlas Manager')

atlas_new_version = mari.actions.create('New Version', 'from atlas_manager.ui import main;tui = main.launch("Mari", dont_show=True);tui.on_new_version()')
mari.menus.addAction(atlas_new_version, 'MainWindow/Atlas Manager')

atlas_publish = mari.actions.create('Publish', 'from atlas_manager.ui import main;tui = main.launch("Mari", dont_show=True);tui.on_publish_scene()')
mari.menus.addAction(atlas_publish, 'MainWindow/Atlas Manager')

atlas_load_template_action = mari.actions.create(
    'Load Template',
    'from atlas_manager.plugins.mari import template; template.import_template()'
)
mari.menus.addAction(atlas_load_template_action, 'MainWindow/Atlas Manager')


