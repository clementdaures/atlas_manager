import os

EXTENSION_DICT = {
    "houdini": [".hip", ".hipnc", ".hiplc"],
    "mari": [".mri"],
    "maya": [".ma", ".mb"],
    "nuke": [".nk"],
    "standalone": [".*"],
    "substance": [".spp"],
}

NAME = os.getenv("ATLAS_DCC").lower()

if NAME == "houdini":
    from atlas_manager.dcc.houdini.main import Dcc
elif NAME == "mari":
    from atlas_manager.dcc.mari.main import Dcc
elif NAME == "maya":
    from atlas_manager.dcc.maya.main import Dcc
elif NAME == "nuke":
    from atlas_manager.dcc.nuke.main import Dcc
elif NAME == "null":
    pass # Null DCC is used for testing purposes.
elif NAME == "standalone":
    from atlas_manager.dcc.standalone.main import Dcc
elif NAME == "substance":
    from atlas_manager.dcc.substance.main import Dcc
else:
    raise ValueError(f"Environment variable 'ATLAS_DCC' value ({NAME} is not matching any defined DCCs.")
