#!/bin/bash
# build.sh - Build script for Acapella
#
# Usage: ./build.sh [options]
# Run ./build.sh --help for available options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
CLEAN=true
GUI_ONLY=false
CLI_ONLY=false
SKIP_DEPS=false
OPEN_APP=false

# Get script directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat << EOF
Usage: $(basename "$0") [options]

Build script for Acapella

Options:
  -c, --clean       Clean build artifacts before building (default: on)
  -n, --no-clean    Skip cleaning build artifacts
  -g, --gui-only    Build GUI only (skip CLI)
  -l, --cli-only    Build CLI only (skip GUI)
  -s, --skip-deps   Skip FFmpeg and model downloads
  -o, --open        Open the app after build (macOS only)
  -h, --help        Show this help message

Examples:
  $(basename "$0")                    # Full build with clean
  $(basename "$0") --gui-only         # Build only the GUI app
  $(basename "$0") --gui-only --open  # Build GUI and open it
  $(basename "$0") --skip-deps        # Build without downloading dependencies
EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -n|--no-clean)
            CLEAN=false
            shift
            ;;
        -g|--gui-only)
            GUI_ONLY=true
            shift
            ;;
        -l|--cli-only)
            CLI_ONLY=true
            shift
            ;;
        -s|--skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        -o|--open)
            OPEN_APP=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate mutually exclusive options
if [[ "$GUI_ONLY" == true && "$CLI_ONLY" == true ]]; then
    log_error "Cannot specify both --gui-only and --cli-only"
    exit 1
fi

# Warn if skipping deps but ffmpeg_bin doesn't exist
if [[ "$SKIP_DEPS" == true && ! -d "$SCRIPT_DIR/ffmpeg_bin" ]]; then
    log_warn "ffmpeg_bin/ not found. FFmpeg will NOT be bundled!"
    log_warn "Run without --skip-deps first to download FFmpeg."
fi

# Change to project directory
cd "$SCRIPT_DIR"

# Clean build artifacts (preserve ffmpeg_bin for caching)
if [[ "$CLEAN" == true ]]; then
    log_info "Cleaning build artifacts..."
    rm -rf dist build
    log_success "Clean complete"
fi

# Build command construction
BUILD_CMD="python3 scripts/build.py"

if [[ "$GUI_ONLY" == true ]]; then
    BUILD_CMD="$BUILD_CMD --gui-only"
fi

if [[ "$CLI_ONLY" == true ]]; then
    BUILD_CMD="$BUILD_CMD --cli-only"
fi

if [[ "$SKIP_DEPS" == true ]]; then
    BUILD_CMD="$BUILD_CMD --skip-ffmpeg --skip-models"
fi

# Run the build
log_info "Starting build..."
log_info "Command: $BUILD_CMD"
echo ""

$BUILD_CMD

echo ""
log_success "Build complete!"

# Report build results
echo ""
log_info "Build artifacts:"

if [[ "$CLI_ONLY" != true && -d "dist/Acapella.app" ]]; then
    GUI_SIZE=$(du -sh "dist/Acapella.app" | cut -f1)
    log_info "  GUI App: dist/Acapella.app ($GUI_SIZE)"
fi

if [[ "$GUI_ONLY" != true && -d "dist/acapella" ]]; then
    CLI_SIZE=$(du -sh "dist/acapella" | cut -f1)
    log_info "  CLI: dist/acapella ($CLI_SIZE)"
fi

# List any archives created
for archive in dist/../*.tar.gz dist/../*.zip; do
    if [[ -f "$archive" ]]; then
        ARCHIVE_SIZE=$(du -sh "$archive" | cut -f1)
        log_info "  Archive: $archive ($ARCHIVE_SIZE)"
    fi
done

# Open the app if requested (macOS only)
if [[ "$OPEN_APP" == true ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        if [[ -d "dist/Acapella.app" ]]; then
            log_info "Opening Acapella.app..."
            open "dist/Acapella.app"
        else
            log_warn "Cannot open app: dist/Acapella.app not found"
            log_warn "Did you build with --cli-only?"
        fi
    else
        log_warn "--open flag is only supported on macOS"
    fi
fi
