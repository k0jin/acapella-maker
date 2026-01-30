"""Command-line interface for Acapella Maker."""

import shutil
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from acapella_maker import __version__
from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import download_audio, is_youtube_url
from acapella_maker.exceptions import AcapellaMakerError, YouTubeDownloadError
from acapella_maker.models.result import ProcessingOptions

DOWNLOADS_DIR = Path.home() / "Downloads"
if not DOWNLOADS_DIR.exists():
    DOWNLOADS_DIR = Path.cwd()


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


def resolve_input_source(input_source: str, console: Console) -> tuple[Path, str | None]:
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
        with spinner_progress(console) as progress:
            task = progress.add_task("Downloading from YouTube...", total=None)
            input_file = download_audio(input_source, Path(temp_dir))
            progress.remove_task(task)
        console.print(f"[green]Downloaded:[/green] {input_file.name}")
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


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Acapella Maker - Extract vocals from audio files."""
    pass


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
    silence_threshold: float = typer.Option(
        30.0,
        "--silence-threshold",
        "-s",
        help="Silence threshold in dB below peak",
        min=0,
        max=100,
    ),
    no_trim: bool = typer.Option(
        False,
        "--no-trim",
        help="Disable silence trimming",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
) -> None:
    """Extract acapella vocals from an audio file or YouTube URL."""
    options = ProcessingOptions(
        silence_threshold_db=silence_threshold,
        trim_silence=not no_trim,
    )

    pipeline = AcapellaPipeline(options)
    temp_dir: str | None = None

    try:
        input_file, temp_dir = resolve_input_source(input_source, console)

        # Set default output to Downloads folder
        if output is None:
            output = DOWNLOADS_DIR / f"{input_file.stem}_acapella.wav"

        with spinner_progress(console) as progress:
            # BPM detection
            task = progress.add_task("Detecting BPM...", total=None)
            bpm = pipeline.detect_bpm_only(input_file)
            progress.remove_task(task)
            console.print(f"[green]BPM:[/green] {bpm}")

            # Vocal extraction
            task = progress.add_task("Extracting vocals (this may take a while)...", total=None)

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

        if verbose:
            console.print(f"[dim]Original duration: {result.original_duration:.1f}s[/dim]")
            console.print(f"[dim]Sample rate: {result.sample_rate}Hz[/dim]")

    except YouTubeDownloadError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AcapellaMakerError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AcapellaMakerError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(130)
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app()
