#!/usr/bin/env python3
"""Build script for creating standalone acapella executables."""

import os
import platform
import shutil
import ssl
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import certifi

# FFmpeg download URLs and checksums
FFMPEG_URLS = {
    "darwin": {
        "url": "https://evermeet.cx/ffmpeg/getrelease/zip",
        "ffprobe_url": "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        "extract": "zip",
    },
    "linux": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        "extract": "tar.xz",
    },
    "win32": {
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "extract": "zip",
    },
}


def get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "win32"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def download_file(url: str, dest: Path, desc: str = "Downloading") -> None:
    """Download a file with progress indication."""
    print(f"{desc}: {url}")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(url, context=ssl_context) as response:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 8192

        with open(dest, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(
                        f"\r  Progress: {pct}% ({downloaded // 1024 // 1024}MB)", end=""
                    )

    print()  # newline after progress


def extract_archive(archive_path: Path, dest_dir: Path, archive_type: str) -> None:
    """Extract an archive to destination directory."""
    print(f"Extracting: {archive_path}")
    dest_dir.mkdir(parents=True, exist_ok=True)

    if archive_type == "zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)
    elif archive_type in ("tar.xz", "tar.gz", "tar"):
        mode = (
            "r:xz"
            if archive_type == "tar.xz"
            else "r:gz"
            if archive_type == "tar.gz"
            else "r"
        )
        with tarfile.open(archive_path, mode) as tf:
            tf.extractall(dest_dir)
    else:
        raise ValueError(f"Unknown archive type: {archive_type}")


def find_ffmpeg_binaries(
    extract_dir: Path, plat: str
) -> tuple[Path | None, Path | None]:
    """Find ffmpeg and ffprobe binaries in extracted directory."""
    ffmpeg_name = "ffmpeg.exe" if plat == "win32" else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if plat == "win32" else "ffprobe"

    ffmpeg_path = None
    ffprobe_path = None

    for root, dirs, files in os.walk(extract_dir):
        root_path = Path(root)
        if ffmpeg_name in files:
            ffmpeg_path = root_path / ffmpeg_name
        if ffprobe_name in files:
            ffprobe_path = root_path / ffprobe_name
        if ffmpeg_path and ffprobe_path:
            break

    return ffmpeg_path, ffprobe_path


def download_ffmpeg(dest_dir: Path) -> None:
    """Download and extract FFmpeg for the current platform."""
    plat = get_platform()
    ffmpeg_info = FFMPEG_URLS.get(plat)

    if not ffmpeg_info:
        raise RuntimeError(f"No FFmpeg download info for platform: {plat}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = dest_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        if plat == "darwin":
            # macOS: Download ffmpeg and ffprobe separately
            ffmpeg_zip = temp_dir / "ffmpeg.zip"
            download_file(ffmpeg_info["url"], ffmpeg_zip, "Downloading FFmpeg")
            extract_archive(ffmpeg_zip, temp_dir / "ffmpeg_extract", "zip")

            ffprobe_zip = temp_dir / "ffprobe.zip"
            download_file(
                ffmpeg_info["ffprobe_url"], ffprobe_zip, "Downloading FFprobe"
            )
            extract_archive(ffprobe_zip, temp_dir / "ffprobe_extract", "zip")

            # Find and copy binaries
            ffmpeg_src = temp_dir / "ffmpeg_extract" / "ffmpeg"
            ffprobe_src = temp_dir / "ffprobe_extract" / "ffprobe"

            if ffmpeg_src.exists():
                shutil.copy2(ffmpeg_src, dest_dir / "ffmpeg")
                os.chmod(dest_dir / "ffmpeg", 0o755)
            if ffprobe_src.exists():
                shutil.copy2(ffprobe_src, dest_dir / "ffprobe")
                os.chmod(dest_dir / "ffprobe", 0o755)

        else:
            # Linux and Windows: Single archive with both binaries
            ext = ffmpeg_info["extract"]
            archive_name = f"ffmpeg.{ext}"
            archive_path = temp_dir / archive_name

            download_file(ffmpeg_info["url"], archive_path, "Downloading FFmpeg")
            extract_archive(archive_path, temp_dir / "extract", ext)

            ffmpeg_path, ffprobe_path = find_ffmpeg_binaries(temp_dir / "extract", plat)

            if ffmpeg_path:
                dest_name = "ffmpeg.exe" if plat == "win32" else "ffmpeg"
                shutil.copy2(ffmpeg_path, dest_dir / dest_name)
                if plat != "win32":
                    os.chmod(dest_dir / dest_name, 0o755)

            if ffprobe_path:
                dest_name = "ffprobe.exe" if plat == "win32" else "ffprobe"
                shutil.copy2(ffprobe_path, dest_dir / dest_name)
                if plat != "win32":
                    os.chmod(dest_dir / dest_name, 0o755)

    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    # Verify binaries exist
    ffmpeg_name = "ffmpeg.exe" if plat == "win32" else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if plat == "win32" else "ffprobe"

    if not (dest_dir / ffmpeg_name).exists():
        raise RuntimeError("Failed to download/extract ffmpeg")
    if not (dest_dir / ffprobe_name).exists():
        print("Warning: ffprobe not found, only ffmpeg was downloaded")

    print(f"FFmpeg binaries installed to: {dest_dir}")


def download_demucs_models() -> None:
    """Pre-download demucs models so they're available for bundling."""
    print("Pre-downloading demucs models...")
    try:
        from demucs.pretrained import get_model

        # This will download the model if not cached
        get_model("htdemucs")
        print("Demucs models downloaded successfully")
    except Exception as e:
        print(f"Warning: Could not pre-download models: {e}")
        print("Models will be downloaded on first run")


def convert_icon_to_icns(project_dir: Path) -> None:
    """Convert icon.png to AppIcon.icns for macOS app bundle."""
    if get_platform() != "darwin":
        return

    icon_png = project_dir / "src" / "acapella" / "gui" / "icon.png"
    icon_icns = project_dir / "src" / "acapella" / "gui" / "AppIcon.icns"

    if not icon_png.exists():
        print(f"Warning: Icon PNG not found: {icon_png}")
        return

    print(f"Converting {icon_png.name} to {icon_icns.name}...")

    iconset_dir = project_dir / "AppIcon.iconset"
    iconset_dir.mkdir(exist_ok=True)

    # Generate all required icon sizes
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    try:
        for size, filename in sizes:
            output = iconset_dir / filename
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size),
                    str(size),
                    str(icon_png),
                    "--out",
                    str(output),
                ],
                check=True,
                capture_output=True,
            )

        # Convert iconset to icns
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icon_icns)],
            check=True,
            capture_output=True,
        )
        print(f"Icon converted: {icon_icns}")

    finally:
        # Clean up iconset directory
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)


def run_pyinstaller(spec_file: Path) -> None:
    """Run PyInstaller with the spec file."""
    print(f"Running PyInstaller with: {spec_file}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller failed with exit code: {result.returncode}")

    print("PyInstaller completed successfully")


def create_archive(dist_dir: Path, output_name: str) -> Path:
    """Create distributable archive from dist directory."""
    plat = get_platform()
    app_dir = dist_dir / "acapella"

    if not app_dir.exists():
        raise RuntimeError(f"Built application not found: {app_dir}")

    if plat == "win32":
        archive_name = f"{output_name}.zip"
        archive_path = dist_dir.parent / archive_name
        print(f"Creating archive: {archive_path}")

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(dist_dir)
                    zf.write(file_path, arc_name)
    else:
        archive_name = f"{output_name}.tar.gz"
        archive_path = dist_dir.parent / archive_name
        print(f"Creating archive: {archive_path}")

        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(app_dir, arcname="acapella")

    print(f"Archive created: {archive_path}")
    return archive_path


def main() -> int:
    """Main build function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build acapella standalone executables"
    )
    parser.add_argument(
        "--skip-ffmpeg",
        action="store_true",
        help="Skip FFmpeg download (use if already installed)",
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip demucs model download",
    )
    parser.add_argument(
        "--cli-only",
        action="store_true",
        help="Build CLI only (skip GUI)",
    )
    parser.add_argument(
        "--gui-only",
        action="store_true",
        help="Build GUI only (skip CLI)",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Output archive name (without extension)",
    )
    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    cli_spec_file = project_dir / "acapella.spec"
    gui_spec_file = project_dir / "acapella_gui.spec"
    ffmpeg_dir = project_dir / "ffmpeg_bin"
    dist_dir = project_dir / "dist"
    plat = get_platform()

    build_cli = not args.gui_only
    build_gui = not args.cli_only  # Build GUI on all platforms

    if build_cli and not cli_spec_file.exists():
        print(f"Error: CLI spec file not found: {cli_spec_file}")
        return 1

    if build_gui and not gui_spec_file.exists():
        print(f"Error: GUI spec file not found: {gui_spec_file}")
        return 1

    # Download FFmpeg
    if not args.skip_ffmpeg:
        print("\n=== Downloading FFmpeg ===")
        download_ffmpeg(ffmpeg_dir)

    # Download demucs models
    if not args.skip_models:
        print("\n=== Downloading Demucs Models ===")
        download_demucs_models()

    # Build CLI
    if build_cli:
        print("\n=== Building CLI ===")
        run_pyinstaller(cli_spec_file)

    # Build GUI
    if build_gui:
        print("\n=== Converting App Icon ===")
        convert_icon_to_icns(project_dir)
        print("\n=== Building GUI App ===")
        run_pyinstaller(gui_spec_file)

    # Create CLI archive
    if build_cli:
        print("\n=== Creating CLI Archive ===")
        plat_name = {"darwin": "macos", "linux": "linux", "win32": "windows"}[plat]
        output_name = args.output_name or f"acapella-{plat_name}"
        archive_path = create_archive(dist_dir, output_name)

    print("\n=== Build Complete ===")
    if build_cli:
        print(f"CLI Executable: {dist_dir / 'acapella'}")
        print(f"CLI Archive: {archive_path}")
    if build_gui:
        print(f"GUI App: {dist_dir / 'Acapella.app'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
