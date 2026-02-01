<#
.SYNOPSIS
    Build script for Acapella Maker

.DESCRIPTION
    Build script for creating standalone Acapella Maker executables on Windows.

.PARAMETER Clean
    Clean build artifacts before building (default: on)

.PARAMETER NoClean
    Skip cleaning build artifacts

.PARAMETER GuiOnly
    Build GUI only (skip CLI)

.PARAMETER CliOnly
    Build CLI only (skip GUI)

.PARAMETER SkipDeps
    Skip FFmpeg and model downloads

.PARAMETER Open
    Open the app after build

.PARAMETER Help
    Show this help message

.EXAMPLE
    .\build.ps1
    Full build with clean

.EXAMPLE
    .\build.ps1 -GuiOnly
    Build only the GUI app

.EXAMPLE
    .\build.ps1 -GuiOnly -Open
    Build GUI and open it

.EXAMPLE
    .\build.ps1 -SkipDeps
    Build without downloading dependencies
#>

param(
    [Alias("c")]
    [switch]$Clean,

    [Alias("n")]
    [switch]$NoClean,

    [Alias("g")]
    [switch]$GuiOnly,

    [Alias("l")]
    [switch]$CliOnly,

    [Alias("s")]
    [switch]$SkipDeps,

    [Alias("o")]
    [switch]$Open,

    [Alias("h")]
    [switch]$Help
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Logging functions with colors
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Log-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Log-Warn {
    param([string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Show-Usage {
    Write-Host @"
Usage: .\build.ps1 [options]

Build script for Acapella Maker

Options:
  -c, -Clean       Clean build artifacts before building (default: on)
  -n, -NoClean     Skip cleaning build artifacts
  -g, -GuiOnly     Build GUI only (skip CLI)
  -l, -CliOnly     Build CLI only (skip GUI)
  -s, -SkipDeps    Skip FFmpeg and model downloads
  -o, -Open        Open the app after build
  -h, -Help        Show this help message

Examples:
  .\build.ps1                    # Full build with clean
  .\build.ps1 -GuiOnly           # Build only the GUI app
  .\build.ps1 -GuiOnly -Open     # Build GUI and open it
  .\build.ps1 -SkipDeps          # Build without downloading dependencies
"@
}

function Get-FolderSize {
    param([string]$Path)
    if (Test-Path $Path) {
        $size = (Get-ChildItem -Path $Path -Recurse -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        if ($size -ge 1GB) {
            return "{0:N1}G" -f ($size / 1GB)
        } elseif ($size -ge 1MB) {
            return "{0:N0}M" -f ($size / 1MB)
        } else {
            return "{0:N0}K" -f ($size / 1KB)
        }
    }
    return "0"
}

function Get-FileSize {
    param([string]$Path)
    if (Test-Path $Path) {
        $size = (Get-Item $Path).Length
        if ($size -ge 1GB) {
            return "{0:N1}G" -f ($size / 1GB)
        } elseif ($size -ge 1MB) {
            return "{0:N0}M" -f ($size / 1MB)
        } else {
            return "{0:N0}K" -f ($size / 1KB)
        }
    }
    return "0"
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Validate mutually exclusive options
if ($GuiOnly -and $CliOnly) {
    Log-Error "Cannot specify both -GuiOnly and -CliOnly"
    exit 1
}

# Default to clean unless -NoClean is specified
$DoClean = -not $NoClean

# Warn if skipping deps but ffmpeg_bin doesn't exist
if ($SkipDeps -and -not (Test-Path "$ScriptDir\ffmpeg_bin")) {
    Log-Warn "ffmpeg_bin/ not found. FFmpeg will NOT be bundled!"
    Log-Warn "Run without -SkipDeps first to download FFmpeg."
}

# Change to project directory
Set-Location $ScriptDir

# Clean build artifacts (preserve ffmpeg_bin for caching)
if ($DoClean) {
    Log-Info "Cleaning build artifacts..."
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    Log-Success "Clean complete"
}

# Build command construction
$BuildArgs = @()

if ($GuiOnly) {
    $BuildArgs += "--gui-only"
}

if ($CliOnly) {
    $BuildArgs += "--cli-only"
}

if ($SkipDeps) {
    $BuildArgs += "--skip-ffmpeg"
    $BuildArgs += "--skip-models"
}

# Run the build
Log-Info "Starting build..."
$BuildCmd = "python scripts/build.py $($BuildArgs -join ' ')"
Log-Info "Command: $BuildCmd"
Write-Host ""

# Execute the build
$process = Start-Process -FilePath "python" -ArgumentList (@("scripts/build.py") + $BuildArgs) -NoNewWindow -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Log-Error "Build failed with exit code $($process.ExitCode)"
    exit $process.ExitCode
}

Write-Host ""
Log-Success "Build complete!"

# Report build results
Write-Host ""
Log-Info "Build artifacts:"

if (-not $CliOnly -and (Test-Path "dist\AcapellaMaker")) {
    $guiSize = Get-FolderSize "dist\AcapellaMaker"
    Log-Info "  GUI App: dist\AcapellaMaker ($guiSize)"
}

if (-not $GuiOnly -and (Test-Path "dist\acapella-maker")) {
    $cliSize = Get-FolderSize "dist\acapella-maker"
    Log-Info "  CLI: dist\acapella-maker ($cliSize)"
}

# List any archives created
Get-ChildItem -Path "." -Filter "*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
    $archiveSize = Get-FileSize $_.FullName
    Log-Info "  Archive: $($_.Name) ($archiveSize)"
}

# Open the app if requested
if ($Open) {
    if (-not $CliOnly -and (Test-Path "dist\AcapellaMaker\AcapellaMaker.exe")) {
        Log-Info "Opening AcapellaMaker..."
        Start-Process "dist\AcapellaMaker\AcapellaMaker.exe"
    } elseif (-not $GuiOnly -and (Test-Path "dist\acapella-maker\acapella-maker.exe")) {
        Log-Info "Opening acapella-maker CLI..."
        Start-Process "cmd" -ArgumentList "/k", "dist\acapella-maker\acapella-maker.exe", "--help"
    } else {
        Log-Warn "Cannot open app: executable not found"
        Log-Warn "Did you build with -CliOnly?"
    }
}
