# II. Detailed Project Structure

> *This document describes the logical organization of the project codebase as a Pixi workspace for the audio release pipeline.*

## Repository Layout

```
audio-forge-opus-one/
├── composizioni/       # Musical workspaces for `Composizioni, Op. 1`.
│   │
│   ├── Op-1_No-1_Believe/                  # No. 1: Believe (Piano).
│   ├── Op-1_No-2_Silence/                  # No. 2: Silence (Piano).
│   ├── Op-1_No-3_Abyss/                    # No. 3: Abyss (Piano, Harp, and Soprano).
│   ├── Op-1_No-4_Through_Pain/             # No. 4: Through Pain (Piano).
│   ├── Op-1_No-5_To-the-Beloved/           # No. 5: To the Beloved (Piano, Soprano, and Contralto).
│   ├── Op-1_No-6_Dreaming/                 # No. 6: Dreaming (Harp).
│   └── Op-1_No-7_Solitude-and-Loneliness/  # No. 7: Solitude and Loneliness (Piano).
│
├── recipes/            # Local conda packages built via `pixi-build` and
│   │                   # declared as workspace or run dependencies.
│   │
│   ├── scripts/        # Audio pipeline CLIs (pixi-build-python recipe).
│   ├── musescore/      # MuseScore 3.7.0 (rattler-build recipe).
│   ├── plugalyzer/     # Offline plugin host (rattler-build recipe).
│   └── duskverb/       # DuskVerb VST3 (rattler-build recipe).
│
├── metadata.toml       # Shared release metadata (used by workspace CLIs).
│
├── pixi.toml           # Workspace manifest: channels, dependencies, and tasks.
│
├── pixi.lock           # Fully resolved and reproducible dependency lockfile.
│
├── LICENSE-CC-BY-4.0   # Full text of the Creative Commons Attribution 4.0
│                       # International License.
│
├── LICENSE-APACHE-2.0  # Full text of the Apache License, Version 2.0.
│
└── NOTICE              # Preferred attribution when reusing Apache-2.0 licensed
                        # portions of this project, plus preserved
                        # NOTICE text from upstream works reused here.
```

Source files are documented with detailed docstrings and/or inline comments to explain the code.

## Workspace Overview

### 1. `composizioni/Op-1_No-*/`

One directory per piece under `composizioni/Op-1_No-*`. Every piece directory follows the same pipeline artifacts; dry MuseScore exports differ for one-instrument pieces versus multi-stem pieces.

**One-instrument pieces** (No. 1, 2, 4, 6, 7):

```
Op-1_No-1_Believe/
├── score.mscz          # MuseScore source score (fetched from score-forge-opus-one).
│
├── score.flac          # MuseScore FLAC export (full score).
│
├── reverbed.flac       # Send/return DuskVerb mix (dry + send * wet).
│
├── normalized.flac     # reverbed.flac after required `--gain` from measure-loudness.
│
└── release.flac        # normalized.flac with Vorbis release tags.
```

**Multi-stem pieces** (No. 3 and No. 5) export one FLAC per part instead of a single `score.flac`:

```
Op-1_No-3_Abyss/
├── score.mscz
│
├── score-Piano.flac    # Per-part MuseScore FLAC exports.
├── score-Harp.flac
├── score-Soprano.flac
│
├── reverbed.flac       # Mixed dry stems + per-stem send * wet.
│
├── normalized.flac
│
└── release.flac
```

No. 5 uses `score-Piano.flac`, `score-Soprano.flac`, and `score-Contralto.flac` the same way.

> **Note:**  
> `*.mscz` and `*.flac` are gitignored. After a fresh clone the piece directories are empty until `fetch-mscz-scores` and the MuseScore export / audio pipeline are run.

### 2. `recipes/scripts/`

Conda package recipe for the audio pipeline CLIs. Exposes five CLI entry points consumed by the Pixi tasks in `pixi.toml`. Pulls `ffmpeg`, `mutagen`, `plugalyzer`, and `duskverb` as run dependencies.

```
scripts/
├── pyproject.toml                      # Hatchling project definition and console script
│                                       # entry points.
│
├── pixi.toml                           # pixi-build-python recipe: host and run dependencies.
│
└── src/scripts/
    ├── paths.py                        # Project root resolution (PIXI_PROJECT_ROOT or
    │                                   # ancestor walk), piece path resolution, and
    │                                   # `metadata.toml` loading.
    │
    ├── fetch_mscz_scores.py            # fetch-mscz-scores CLI: downloads each local
    │                                   # piece's `score.mscz` from score-forge-opus-one.
    │
    ├── reverb/                         # reverb CLI package.
    │   ├── main.py                     # CLI entry: routes one-instrument vs No. 3 / No. 5.
    │   ├── domain.py                   # Shared Plugalyzer wet render and ffmpeg amix.
    │   ├── single.py                   # One-instrument: `score.flac` + positional send.
    │   ├── no3.py                      # No. 3: Piano / Harp / Soprano stems;
    │   │                               # narrow balance Piano L10 / Harp R10 /
    │   │                               # Soprano C.
    │   └── no5.py                      # No. 5: Piano / Soprano / Contralto stems;
                                        # narrow balance Soprano L10 / Piano C /
                                        # Contralto R10.
    │
    ├── normalize_loudness.py           # normalize-loudness CLI: required `--gain`
    │                                   # (from measure-loudness) applied to
    │                                   # `reverbed.flac` → `normalized.flac` (48 kHz).
    │
    ├── measure_loudness.py             # measure-loudness CLI: measures I/TP/LRA of
    │                                   # one FLAC path (e.g. reverbed / normalized)
    │                                   # and prints Recommended `--gain=…`.
    │
    └── write_flac_metadata.py          # write-flac-metadata CLI: copies `normalized.flac`
                                        # to `release.flac` with tags from `metadata.toml`.
```

Piece-oriented CLIs accept a bare directory name (for example `Op-1_No-1_Believe`) and resolve paths relative to the workspace root. They expect the fixed file names from the piece layout above and will fail if those names are missing or renamed. They share `paths.py` for consistent project-root discovery and `metadata.toml` access.

### 3. `recipes/musescore/`

Conda packaging recipe for MuseScore 3.7.0. Provides the `mscore` binary (with `musescore` and `musescore3` symlinks) for exporting `score.mscz` to FLAC.

```
musescore/
├── pixi.toml           # pixi-build-rattler-build package manifest.
│
├── recipe.yaml         # rattler-build recipe: git source, host and run dependencies.
│
└── build.sh            # CMake release build script. Caps parallel jobs to nproc/4 to
                        # reduce OOM risk; installs `mscore` and symlinks `musescore` and
                        # `musescore3` into PREFIX/bin.
```

### 4. `recipes/plugalyzer/`

Conda packaging recipe for Plugalyzer 0.5.0. Provides the `plugalyzer` binary used by the reverb CLI to render a Bus Mode (100% wet) DuskVerb stem offline.

```
plugalyzer/
├── pixi.toml           # pixi-build-rattler-build package manifest.
│
└── recipe.yaml         # rattler-build recipe: upstream Linux zip, install into PREFIX/bin.
```

### 5. `recipes/duskverb/`

Conda packaging recipe for DuskVerb 0.7.2. Installs the VST3 (and LV2) bundle under the environment prefix for Plugalyzer to load during reverb.

```
duskverb/
├── pixi.toml           # pixi-build-rattler-build package manifest.
│
└── recipe.yaml         # rattler-build recipe: upstream Linux zip, install VST3/LV2
                        # under PREFIX/lib.
```
