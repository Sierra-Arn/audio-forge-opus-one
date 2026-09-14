# I. Dependencies Overview

> *This document describes the runtime dependencies required by Audio Forge for Opus One — Pixi, build backends, and workspace packages.*

## System Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| Pixi | [prefix‑dev/pixi](https://github.com/prefix-dev/pixi) | Package and environment manager | 1. Resolves and installs conda dependencies. <br>2. Manages the project's virtual environment and lockfile. <br>3. Acts as the project's task runner. |
| pixi-build-python | [prefix‑dev/pixi](https://github.com/prefix-dev/pixi) | Pixi build backend for Python packages | Builds the `scripts` conda package from `pyproject.toml`. |
| pixi-build-rattler-build | [prefix‑dev/pixi](https://github.com/prefix-dev/pixi) | Pixi build backend for rattler-build recipes | Builds the `musescore`, `duskverb`, and `plugalyzer` conda packages from `recipe.yaml` files. |

## Pixi Dependencies

| Dependency | Source | What it is | Role in the project | Upstream / runtime repositories |
|---|---|---|---|---|
| `scripts` | [recipes/scripts/<br>pixi.toml](../recipes/scripts/pixi.toml) | Python audio pipeline CLIs | Fetches MuseScore sources; applies send/return DuskVerb reverb; measures I/TP/LRA and recommends `--gain`; applies that `--gain` via `normalize-loudness`; writes FLAC release metadata. | - [python/cpython](https://github.com/python/cpython)<br>- [pypa/hatch](https://github.com/pypa/hatch)<br>- [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg)<br>- [quodlibet/mutagen](https://github.com/quodlibet/mutagen) |
| `musescore` | [recipes/musescore/<br>pixi.toml](../recipes/musescore/pixi.toml) | Music notation application | Exports source scores to FLAC (`score.flac` or per-part `score-<Part>.flac`). | - [Jojo‑Schmitz/MuseScore](https://github.com/Jojo-Schmitz/MuseScore) |
| `plugalyzer` | [recipes/plugalyzer/<br>pixi.toml](../recipes/plugalyzer/pixi.toml) | Command-line audio plugin host | Offline-renders DuskVerb (Bus Mode / 100% wet) for the reverb pipeline. | - [CrushedPixel/Plugalyzer](https://github.com/CrushedPixel/Plugalyzer) |
| `duskverb` | [recipes/duskverb/<br>pixi.toml](../recipes/duskverb/pixi.toml) | Algorithmic reverb VST3 plugin | Bright Hall preset used as the send/return reverb engine. | - [dusk-audio/dusk-audio-plugins](https://github.com/dusk-audio/dusk-audio-plugins) |
