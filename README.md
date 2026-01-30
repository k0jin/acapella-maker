# Acapella Maker

Extract acapella vocals from audio files with BPM detection and silence trimming.

## Installation

```bash
pip install -e .
```

**System requirements:** ffmpeg, libsndfile

## Usage

```bash
# Extract vocals
acapella-maker extract song.mp3

# With options
acapella-maker extract song.mp3 -o vocals.wav --silence-threshold 40

# BPM detection only
acapella-maker bpm song.mp3
```

## Options

- `-o, --output PATH` - Output file path (default: `<input>_acapella.wav`)
- `-s, --silence-threshold DB` - Silence threshold in dB (default: 30)
- `--no-trim` - Disable silence trimming
- `-v, --verbose` - Verbose output
