# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Acapella GUI."""

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
            # Bundle to hub/checkpoints/ so TORCH_HOME can find them
            model_paths.append((str(model_file), "hub/checkpoints"))

    return model_paths


# Collect data files
datas = []

# Add demucs remote directory for model signatures and files.txt
try:
    import demucs
    demucs_path = Path(demucs.__file__).parent
    remote_dir = demucs_path / "remote"
    if remote_dir.exists():
        # Include all files (yaml configs and files.txt)
        for f in remote_dir.iterdir():
            if f.is_file():
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

# Collect all rich submodules (for unicode data)
hiddenimports += collect_submodules("rich")

# Collect PySide6 data files (plugins, etc.)
datas += collect_data_files("PySide6")

# Collect torch data files
datas += collect_data_files("torch")

# Collect rich data files (unicode data)
datas += collect_data_files("rich")

# Include certifi certificates
import certifi
datas.append((certifi.where(), "certifi"))

# Bundle pre-downloaded demucs models
datas += find_demucs_models()

# Collect PySide6 binaries/dynamic libs
binaries = []
binaries += collect_dynamic_libs("PySide6")

# Get spec directory for pathex
spec_dir = Path(SPECPATH)

# Check for bundled ffmpeg binaries
ffmpeg_dir = spec_dir / "ffmpeg_bin"
if ffmpeg_dir.exists():
    if sys.platform == "win32":
        ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
        ffprobe_exe = ffmpeg_dir / "ffprobe.exe"
    else:
        ffmpeg_exe = ffmpeg_dir / "ffmpeg"
        ffprobe_exe = ffmpeg_dir / "ffprobe"

    if ffmpeg_exe.exists():
        binaries.append((str(ffmpeg_exe), "."))
    if ffprobe_exe.exists():
        binaries.append((str(ffprobe_exe), "."))

src_dir = spec_dir / "src"

a = Analysis(
    ["src/acapella/gui/__init__.py"],
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
    name="Acapella",
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
    icon="src/acapella/gui/icon.ico" if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Acapella",
)

# macOS app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Acapella.app",
        icon="src/acapella/gui/AppIcon.icns",
        bundle_identifier="com.acapella.app",
        info_plist={
            "CFBundleName": "Acapella",
            "CFBundleDisplayName": "Acapella",
            "CFBundleVersion": "0.1.0",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,  # Support dark mode
        },
    )
