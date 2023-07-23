# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['Code Files\\GUI.py'],
    pathex=[],
    binaries=[('./Code Files/NKTPDLL.dll', '.')],
    datas=[('./Code Files/NKTP_DLL.py', '.'), ('./Code Files/connections.json', '.'), ('./Code Files/LASER.py', '.'), ('./Code Files/OSA.py', '.'), ('./Code Files/Operator.py', '.'), ('./Code Files/GUI.py', '.'), ('./Code Files/allantools.py', '.'), ('./Code Files/Analyzer.py', '.'), ('./Code Files/Interactive_Graph.py', '.')],
    hiddenimports=[],
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
    name='GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
