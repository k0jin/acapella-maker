# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for acapella-maker."""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Determine paths
spec_dir = Path(SPECPATH)
src_dir = spec_dir / "src"

# Collect hidden imports for PyTorch and demucs
hidden_imports = [
    # PyTorch
    "torch",
    "torch.nn",
    "torch.nn.functional",
    "torch.utils",
    "torch.utils.data",
    # Demucs
    "demucs",
    "demucs.apply",
    "demucs.pretrained",
    "demucs.hdemucs",
    "demucs.htdemucs",
    "demucs.states",
    "demucs.spec",
    "demucs.utils",
    # Audio processing
    "librosa",
    "soundfile",
    "numpy",
    # CLI
    "typer",
    "rich",
    "click",
    # YouTube downloading
    "yt_dlp",
    "yt_dlp.extractor",
    "yt_dlp.downloader",
    "yt_dlp.postprocessor",
    # SSL/certifi
    "certifi",
    # Other
    "tqdm",
    "scipy",
    "scipy.signal",
    "scipy.io",
    "scipy.io.wavfile",
]

# Collect all submodules for complex packages
hidden_imports += collect_submodules("demucs")
hidden_imports += collect_submodules("yt_dlp")

# Collect data files
datas = []

# Include certifi certificates
import certifi
datas.append((certifi.where(), "certifi"))

# Include demucs remote directory (for model loading)
try:
    import demucs
    demucs_path = Path(demucs.__file__).parent
    remote_dir = demucs_path / "remote"
    if remote_dir.exists():
        datas.append((str(remote_dir), "demucs/remote"))
except ImportError:
    pass

# Collect torch data files (needed for proper operation)
datas += collect_data_files("torch")

# Binaries - ffmpeg will be added by build script
binaries = []

# Check for bundled ffmpeg
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

# Analysis
a = Analysis(
    [str(src_dir / "acapella_maker" / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary GUI libraries
        "tkinter",
        "matplotlib",
        "PIL",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        # Exclude test frameworks
        "pytest",
        # Note: unittest is needed by torch, do not exclude
        # Exclude development tools
        "IPython",
        "jupyter",
    ],
    noarchive=False,
    optimize=0,
)

# Bundle as directory (not single file - better for large apps)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="acapella-maker",
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
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="acapella-maker",
)
