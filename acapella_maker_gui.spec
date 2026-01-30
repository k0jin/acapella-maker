# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Acapella Maker GUI."""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Find demucs pretrained models directory
def find_demucs_models():
    """Find demucs pretrained model files."""
    import demucs.pretrained

    # Get the demucs package directory
    demucs_dir = Path(demucs.pretrained.__file__).parent

    # Models are typically cached in ~/.cache/torch/hub/checkpoints
    # or downloaded to the demucs package directory
    model_paths = []

    # Check for models in common locations
    cache_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    if cache_dir.exists():
        for model_file in cache_dir.glob("*.th"):
            model_paths.append((str(model_file), "torch_cache"))

    return model_paths


# Collect data files
datas = []

# Add demucs remote directory for model signatures
try:
    import demucs
    demucs_path = Path(demucs.__file__).parent
    remote_dir = demucs_path / "remote"
    if remote_dir.exists():
        for f in remote_dir.glob("*.yaml"):
            datas.append((str(f), "demucs/remote"))
except ImportError:
    pass

# Collect hidden imports for audio processing
hiddenimports = [
    "soundfile",
    "librosa",
    "librosa.util",
    "scipy.signal",
    "scipy.fft",
    "numpy",
    "torch",
    "torchaudio",
    "demucs",
    "demucs.pretrained",
    "demucs.apply",
    "demucs.audio",
    "demucs.hdemucs",
    "demucs.htdemucs",
    "yt_dlp",
    "certifi",
]

# Collect all PySide6 submodules
hiddenimports += collect_submodules("PySide6")

# Collect all demucs submodules
hiddenimports += collect_submodules("demucs")

# Collect all yt_dlp submodules
hiddenimports += collect_submodules("yt_dlp")

# Collect PySide6 data files (plugins, etc.)
datas += collect_data_files("PySide6")

# Collect torch data files
datas += collect_data_files("torch")

# Include certifi certificates
import certifi
datas.append((certifi.where(), "certifi"))

# Collect PySide6 binaries/dynamic libs
binaries = []
binaries += collect_dynamic_libs("PySide6")

# Get spec directory for pathex
spec_dir = Path(SPECPATH)
src_dir = spec_dir / "src"

a = Analysis(
    ["src/acapella_maker/gui/__init__.py"],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PIL",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        # Note: unittest is needed by torch, do not exclude
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
    [],
    exclude_binaries=True,
    name="AcapellaMaker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI mode, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AcapellaMaker",
)

# macOS app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Acapella Maker.app",
        icon=None,  # Add icon path here if available
        bundle_identifier="com.acapellamaker.app",
        info_plist={
            "CFBundleName": "Acapella Maker",
            "CFBundleDisplayName": "Acapella Maker",
            "CFBundleVersion": "0.1.0",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,  # Support dark mode
        },
    )
