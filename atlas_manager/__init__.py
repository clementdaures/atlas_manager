import os
from pathlib import Path
from importlib import reload
from atlas_manager.objects import guard

def initialize(dcc_name, common_folder=None):
    os.environ["ATLAS_DCC"] = dcc_name
    parent_folder = Path(__file__).parent.parent / "atlas_manager" / "external"
    os.environ["ATLAS_EXTERNAL_SOURCES"] = parent_folder.as_posix()
    guard.Guard.set_dcc(dcc_name) # force the guard to use the dcc name
    # the reload is necessary to make sure the dcc is reloaded
    # this makes sure when different dcc's are used in the same python session
    # for example, Maya and trigger.
    import atlas_manager.objects.main
    reload(atlas_manager.objects.main)
    return atlas_manager.objects.main.Main(common_folder=common_folder)

    # get the installation folder of atlas_manager
    # this is necessary to get the default settings
    # and other resources
