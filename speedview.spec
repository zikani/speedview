# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules("speedview") + [
    "PyQt5.QtSvg",
    "PyQt5.QtXml",
]

if sys.platform == "win32":
    hiddenimports += [
        "win32com.client",
        "winshell",
    ]

datas = [
    ("speedview/ui/resources/speedview.png", "speedview/ui/resources"),
    ("speedview/ui/resources/speedview.ico", "speedview/ui/resources"),
    ("speedview/ui/resources/speedview.icns", "speedview/ui/resources"),
    ("speedview/ui/resources/speedview_icon.svg", "speedview/ui/resources"),
    ("CHANGELOG.md", "."),
]

if sys.platform == "win32" and os.path.exists("speedview/ui/resources/speedview.ico"):
    app_icon = "speedview/ui/resources/speedview.ico"
elif sys.platform == "darwin" and os.path.exists("speedview/ui/resources/speedview.icns"):
    app_icon = "speedview/ui/resources/speedview.icns"
elif sys.platform.startswith("linux") and os.path.exists("speedview/ui/resources/speedview.png"):
    app_icon = "speedview/ui/resources/speedview.png"
else:
    app_icon = None

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="SpeedView",
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
        icon=app_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="SpeedView",
    )
    app = BUNDLE(
        coll,
        name="SpeedView.app",
        icon=app_icon,
        bundle_identifier="com.speedview.app",
    )
else:
    # Program Files / extracted onedir layout for clean upgrades and auto-updating
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="SpeedView",
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
        icon=app_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="SpeedView",
    )
