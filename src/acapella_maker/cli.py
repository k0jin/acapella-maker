"""Command-line interface for Acapella Maker."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from acapella_maker import __version__
from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.exceptions import AcapellaMakerError
from acapella_maker.models.result import ProcessingOptions

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


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
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
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file (MP3, WAV, FLAC, etc.)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: <input>_acapella.wav)",
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
    """Extract acapella vocals from an audio file."""
    options = ProcessingOptions(
        silence_threshold_db=silence_threshold,
        trim_silence=not no_trim,
    )

    pipeline = AcapellaPipeline(options)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
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

    except AcapellaMakerError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(130)


@app.command()
def bpm(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        readable=True,
    ),
) -> None:
    """Detect BPM of an audio file."""
    pipeline = AcapellaPipeline()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing...", total=None)
            detected_bpm = pipeline.detect_bpm_only(input_file)
            progress.remove_task(task)

        console.print(f"[green]BPM:[/green] {detected_bpm}")

    except AcapellaMakerError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
