"""Extract the textures."""

import math
from pathlib import Path

import substance_painter

from atlas_manager.dcc.extract_core import ExtractCore


class Textures(ExtractCore):
    """Extract Textures."""

    nice_name = "Texture Bundle"
    color = (50, 150, 50)
    bundled = True
    bundle_match_id = 8004

    def __init__(self):
        global_exposed_settings = {
            # first item will be the default
            "export_preset": {
                "display_name": "Export Preset",
                "type": "combo",
                "items": ["ANDHA_EXTRA", "ANDHA_SIMPLE", "ANDHA_UTILS"],
                "value": "ANDHA_EXTRA"
            },
            "file_format": {
                "display_name": "File Format",
                "type": "combo",
                "items": ["bmp", "ico", "jpg", "jng", "pbm", "pgm", "png", "ppm", "tga",
                          "tif", "wap", "xpn", "gif", "hdr", "exr", "j2k", "jp2", "pfm",
                          "webp", "jxr", "psd", "sbsar"],
                "value": "exr"
            },
            "bit_depth": {
                "display_name": "Bit Depth",
                "type": "combo",
                "items": ["8", "16", "16f", "32f"],
                "value": "16f"
            },
            "texture_resolution": {
                "display_name": "Texture Resolution",
                "type": "combo",
                "items": ["", "128", "256", "512", "1024", "2048", "4096"],
                "value": "4096"
            },  # if not defined, it will use the project resolution
            "export_height_maps": {
                "display_name": "Export Height Maps",
                "type": "combo",
                "items": ["yes", "no"],
                "value": "yes"
            },
            "height_file_format": {
                "display_name": "Height File Format",
                "type": "combo",
                "items": ["bmp", "ico", "jpg", "jng", "pbm", "pgm", "png", "ppm", "tga",
                          "tif", "wap", "xpn", "gif", "hdr", "exr", "j2k", "jp2", "pfm",
                          "webp", "jxr", "psd", "sbsar"],
                "value": "exr"
            },
            "height_bit_depth": {
                "display_name": "Height Bit Depth",
                "type": "combo",
                "items": ["8", "16", "16f", "32f"],
                "value": "32f"
            },
            "height_texture_resolution": {
                "display_name": "Height Texture Resolution",
                "type": "combo",
                "items": ["", "128", "256", "512", "1024", "2048", "4096"],
                "value": "4096"
            }
        }
        super().__init__(global_exposed_settings=global_exposed_settings)

    def _extract_default(self):
        """Extract the textures."""
        if not substance_painter.project.is_open():
            raise ValueError("No project is open.")

        _str_directory = self.resolve_output()
        bundle_directory = Path(_str_directory)
        bundle_directory.mkdir(parents=True, exist_ok=True)

        export_preset = substance_painter.resource.ResourceID(
            context="your_assets", name=self.global_settings.get("export_preset"))

        # List all the Texture Sets:
        for texture_set in substance_painter.textureset.all_texture_sets():
            for stack in texture_set.all_stacks():
                # Get stack name
                stack_name = str(stack)

                # Get stack resolution (in powers of 2)
                material = stack.material()
                defined_res = self.global_settings.get("texture_resolution")
                if defined_res:
                    resolution = int(defined_res)
                else:
                    resolution = material.get_resolution().width
                logarithmic_size = int(math.log2(resolution))

                # Export main textures (excluding height maps)
                export_list = [{"rootPath": stack_name}]
                self.__export(
                    bundle_directory.as_posix(),
                    export_list,
                    export_preset,
                    stack_name,
                    logarithmic_size=logarithmic_size,
                    export_height=False
                )

                # Export height maps separately if enabled
                if self.global_settings.get("export_height_maps") == "yes":
                    height_defined_res = self.global_settings.get("height_texture_resolution")
                    if height_defined_res:
                        height_resolution = int(height_defined_res)
                    else:
                        height_resolution = material.get_resolution().width
                    height_logarithmic_size = int(math.log2(height_resolution))

                    self.__export(
                        bundle_directory.as_posix(),
                        export_list,
                        export_preset,
                        stack_name,
                        logarithmic_size=height_logarithmic_size,
                        export_height=True
                    )

    def __export(self, folder_path, export_list, export_preset, stack_name, logarithmic_size=12, export_height=False):
        # Choose settings based on whether we're exporting height maps
        if export_height:
            file_format = self.global_settings.get("height_file_format")
            bit_depth = self.global_settings.get("height_bit_depth")
        else:
            file_format = self.global_settings.get("file_format")
            bit_depth = self.global_settings.get("bit_depth")

        export_config = {
                "exportShaderParams" : False,
                "exportPath"          : folder_path,
                "exportList"          : export_list,
                "defaultExportPreset"   : export_preset.url(),
                "exportParameters"     : [
                    {
                        "parameters"    : {
                            "paddingAlgorithm": "infinite",
                            "sizeLog2" : logarithmic_size,
                            "fileFormat" : file_format,
                            "bitDepth": str(bit_depth)
                        }
                    }
                ]
            }

        substance_painter.export.export_project_textures(export_config)

        # Clean up unwanted maps after export
        if not export_height:
            # Remove height/displacement/bump maps after main export
            self.__cleanup_maps(folder_path, ["height", "displacement", "bump"], stack_name)

        return

    def __cleanup_maps(self, folder_path, map_names, stack_name):
        """Remove exported files that match specified map names."""
        folder = Path(folder_path)
        if not folder.exists():
            return

        for file_path in folder.glob("*"):
            if file_path.is_file():
                file_name_lower = file_path.stem.lower()

                if stack_name.lower() in file_name_lower:
                    for map_name in map_names:
                        if map_name in file_name_lower:
                            try:
                                file_path.unlink()
                                print(f"Removed map: {file_path.name}")
                            except Exception as e:
                                print(f"Failed to remove {file_path.name}: {e}")
                            break

    def __keep_only_maps(self, folder_path, map_names):
        """Remove all files except those matching specified map names."""
        folder = Path(folder_path)
        if not folder.exists():
            return

        for file_path in folder.glob("*"):
            if file_path.is_file():
                file_name_lower = file_path.stem.lower()
                should_keep = any(map_name in file_name_lower for map_name in map_names)

                if not should_keep:
                    try:
                        file_path.unlink()
                        print(f"Removed non-height map: {file_path.name}")
                    except Exception as e:
                        print(f"Failed to remove {file_path.name}: {e}")