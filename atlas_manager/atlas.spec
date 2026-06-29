```python
# -*- mode: python ; coding: utf-8 -*-

st_a = Analysis(
    ['dcc\\standalone\\atlas_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui\\theme', 'ui\\theme'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

st_pyz = PYZ(st_a.pure)

st_exe = EXE(
    st_pyz,
    st_a.scripts,
    [],
    exclude_binaries=True,
    name='atlas_standalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui\\theme\\rc\\atlas_main.ico',
)

dcc_a = Analysis(
    ['dcc\\dcc_install.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

dcc_pyz = PYZ(dcc_a.pure)

dcc_exe = EXE(
    dcc_pyz,
    dcc_a.scripts,
    [],
    exclude_binaries=True,
    name='install_dccs',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    st_exe,
    st_a.binaries,
    st_a.datas,

    dcc_exe,
    dcc_a.binaries,
    dcc_a.datas,

    strip=False,
    upx=True,
    upx_exclude=[],
    name='atlas',
)
```
