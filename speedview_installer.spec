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
    ("speedview/ui/resources/speedview_icon.svg", "speedview/ui/resources"),
    ("CHANGELOG.md", "."),
]

payload_root = os.path.abspath(os.path.join("dist", "SpeedView"))
if os.path.isdir(payload_root):
    for root, _dirs, files in os.walk(payload_root):
        for fname in files:
            src_path = os.path.join(root, fname)
            rel_dir = os.path.relpath(root, payload_root)
            target_dir = "payload" if rel_dir == "." else os.path.join("payload", rel_dir)
            datas.append((src_path, target_dir))

if sys.platform == "win32" and os.path.exists("speedview/ui/resources/speedview.ico"):
    setup_icon = "speedview/ui/resources/speedview.ico"
elif os.path.exists("speedview/ui/resources/speedview.png"):
    setup_icon = "speedview/ui/resources/speedview.png"
else:
    setup_icon = None

a = Analysis(
    ["installer.py"],
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SpeedView-Setup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=setup_icon,
    uac_admin=(sys.platform == "win32"),
)
