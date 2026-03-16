# EnigmaMachineSimulator.spec
# PyInstaller spec for the Enigma Machine Simulator.
#
# Build (from the project root with the venv active):
#   Linux/macOS:  pyinstaller EnigmaMachineSimulator.spec
#   Windows:      pyinstaller EnigmaMachineSimulator.spec
#
# Output: dist/EnigmaMachineSimulator  (Linux/macOS)
#         dist/EnigmaMachineSimulator.exe  (Windows)

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle the entire assets/ and sounds/ folders.
        # Each tuple is (source_glob_or_dir, destination_folder_inside_bundle).
        ('assets',  'assets'),
        ('sounds',  'sounds'),
    ],
    hiddenimports=[
        # pygame sub-modules that PyInstaller may miss via static analysis.
        'pygame.mixer',
        'pygame.font',
        'pygame.image',
        'pygame.gfxdraw',
        'pygame.display',
        'pygame.event',
        'pygame.time',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused heavy packages to keep the bundle lean.
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xml',
        'pydoc',
    ],
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
    name='EnigmaMachineSimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # --windowed: no terminal window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific: embed an icon if one is available.
    # icon='assets/icon.ico',  # uncomment and supply a .ico to set the exe icon
)
