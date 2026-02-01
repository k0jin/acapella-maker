"""Command-line interface for Acapella Maker."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from acapella_maker import __version__
from acapella_maker.config import (
    Config,
    get_config,
    get_config_path,
    init_config,
    load_config,
)
from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import download_audio, is_youtube_url
from acapella_maker.exceptions import AcapellaMakerError, YouTubeDownloadError
from acapella_maker.logging_config import get_logger, setup_logging
from acapella_maker.models.result import ProcessingOptions

logger = get_logger(__name__)


def spinner_progress(console: Console) -> Progress:
    """Create a spinner progress display."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


app = typer.Typer(
    name="acapella-maker",
    help="Extract acapella vocals from audio files.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"acapella-maker v{__version__}")
        raise typer.Exit()


def resolve_input_source(
    input_source: str, console: Console
) -> tuple[Path, str | None]:
    """Resolve input source to a file path, downloading from YouTube if needed.

    Args:
        input_source: Local file path or YouTube URL.
        console: Rich console for output.

    Returns:
        Tuple of (input_file_path, temp_dir_to_cleanup_or_none)

    Raises:
        typer.Exit: If file not found or not a file.
        YouTubeDownloadError: If YouTube download fails.
    """
    if is_youtube_url(input_source):
        temp_dir = tempfile.mkdtemp(prefix="acapella_maker_")
        logger.info("Downloading from YouTube: %s", input_source)
        with spinner_progress(console) as progress:
            task = progress.add_task("Downloading from YouTube...", total=None)
            input_file = download_audio(input_source, Path(temp_dir))
            progress.remove_task(task)
        console.print(f"[green]Downloaded:[/green] {input_file.name}")
        logger.info("Downloaded to: %s", input_file)
        return input_file, temp_dir
    else:
        input_file = Path(input_source)
        if not input_file.exists():
            console.print(f"[red]Error:[/red] File not found: {input_file}")
            raise typer.Exit(1)
        if not input_file.is_file():
            console.print(f"[red]Error:[/red] Not a file: {input_file}")
            raise typer.Exit(1)
        return input_file, None


def get_default_output_dir() -> Path:
    """Get the default output directory from config."""
    config = get_config()
    return config.output.get_default_directory()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose (DEBUG) logging to stderr.",
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        help="Write logs to this file.",
    ),
) -> None:
    """Acapella Maker - Extract vocals from audio files."""
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    # Load config and set up logging
    config = get_config()

    level = "DEBUG" if verbose else config.logging.level
    file_path = log_file or (Path(config.logging.file) if config.logging.file else None)

    setup_logging(
        level=level,
        log_file=file_path,
        console_output=verbose,
    )

    logger.debug("Loaded config from %s", get_config_path())


@app.command()
def extract(
    input_source: str = typer.Argument(
        ...,
        help="Input audio file path or YouTube URL",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: ~/Downloads/<input>_acapella.wav)",
    ),
    silence_threshold: Optional[float] = typer.Option(
        None,
        "--silence-threshold",
        "-s",
        help="Silence threshold in dB below peak (default from config: 30.0)",
        min=0,
        max=100,
    ),
    no_trim: bool = typer.Option(
        False,
        "--no-trim",
        help="Disable silence trimming",
    ),
) -> None:
    """Extract acapella vocals from an audio file or YouTube URL."""
    config = get_config()

    # Use config defaults if not specified
    threshold = (
        silence_threshold
        if silence_threshold is not None
        else config.audio.silence_threshold_db
    )
    trim_silence = config.audio.trim_silence and not no_trim

    options = ProcessingOptions(
        silence_threshold_db=threshold,
        trim_silence=trim_silence,
        fade_in_ms=config.audio.fade_in_ms,
        buffer_before_ms=config.audio.buffer_before_ms,
    )

    pipeline = AcapellaPipeline(options)
    temp_dir: str | None = None

    try:
        input_file, temp_dir = resolve_input_source(input_source, console)

        # Set default output to configured directory
        if output is None:
            output_dir = config.output.get_default_directory()
            output = output_dir / f"{input_file.stem}_acapella.wav"

        logger.info("Processing %s -> %s", input_file, output)

        with spinner_progress(console) as progress:
            # BPM detection
            task = progress.add_task("Detecting BPM...", total=None)
            bpm = pipeline.detect_bpm_only(input_file)
            progress.remove_task(task)
            console.print(f"[green]BPM:[/green] {bpm}")

            # Vocal extraction
            task = progress.add_task(
                "Extracting vocals (this may take a while)...", total=None
            )

            # Create new pipeline for full processing
            result = pipeline.process(input_file, output)
            progress.remove_task(task)

        # Print results
        console.print()
        console.print("[bold green]Done![/bold green]")
        console.print(f"[green]Output:[/green] {result.output_path}")
        console.print(f"[green]Duration:[/green] {result.trimmed_duration:.1f}s")

        if options.trim_silence and result.silence_trimmed_ms > 0:
            console.print(
                f"[green]Silence trimmed:[/green] {result.silence_trimmed_ms:.0f}ms"
            )

        logger.info("Extraction complete: %s", result.output_path)

    except YouTubeDownloadError as e:
        logger.error("YouTube download failed: %s", e)
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AcapellaMakerError as e:
        logger.error("Processing failed: %s", e)
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(130)
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.command()
def bpm(
    input_source: str = typer.Argument(
        ...,
        help="Input audio file path or YouTube URL",
    ),
) -> None:
    """Detect BPM of an audio file or YouTube URL."""
    pipeline = AcapellaPipeline()
    temp_dir: str | None = None

    try:
        input_file, temp_dir = resolve_input_source(input_source, console)

        with spinner_progress(console) as progress:
            task = progress.add_task("Analyzing...", total=None)
            detected_bpm = pipeline.detect_bpm_only(input_file)
            progress.remove_task(task)

        console.print(f"[green]BPM:[/green] {detected_bpm}")

    except YouTubeDownloadError as e:
        logger.error("YouTube download failed: %s", e)
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AcapellaMakerError as e:
        logger.error("BPM detection failed: %s", e)
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(130)
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.command("config")
def config_cmd(
    show: bool = typer.Option(
        False,
        "--show",
        help="Display current configuration",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Create default configuration file",
    ),
    path: bool = typer.Option(
        False,
        "--path",
        help="Show configuration file path",
    ),
) -> None:
    """Manage configuration settings."""
    config_path = get_config_path()

    if path:
        console.print(str(config_path))
        return

    if init:
        if config_path.exists():
            console.print(f"[yellow]Config file already exists:[/yellow] {config_path}")
            raise typer.Exit(1)
        created_path = init_config()
        console.print(f"[green]Created config file:[/green] {created_path}")
        return

    if show:
        config = load_config()

        table = Table(title="Configuration", show_header=True)
        table.add_column("Section", style="cyan")
        table.add_column("Setting", style="green")
        table.add_column("Value", style="white")

        # Audio settings
        table.add_row(
            "audio", "silence_threshold_db", str(config.audio.silence_threshold_db)
        )
        table.add_row("audio", "trim_silence", str(config.audio.trim_silence))
        table.add_row("audio", "fade_in_ms", str(config.audio.fade_in_ms))
        table.add_row("audio", "buffer_before_ms", str(config.audio.buffer_before_ms))

        # Output settings
        table.add_row(
            "output",
            "default_directory",
            config.output.default_directory or "(~/Downloads)",
        )
        table.add_row("output", "filename_template", config.output.filename_template)

        # Logging settings
        table.add_row("logging", "level", config.logging.level)
        table.add_row("logging", "file", config.logging.file or "(none)")

        console.print()
        console.print(table)
        console.print()
        console.print(f"[dim]Config file: {config_path}[/dim]")
        if not config_path.exists():
            console.print("[dim]Config file does not exist (using defaults)[/dim]")
        return

    # No option specified, show help
    console.print("Use --show, --init, or --path. See --help for details.")


if __name__ == "__main__":
    app()
