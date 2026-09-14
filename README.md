# Audio Forge for Opus One

*A Pixi workspace for building publication-ready audio files of «Sierra Arn — Composizioni, Op. 1» from MuseScore sources.*

## Project Structure at a Glance

```
audio-forge-opus-one/
├── composizioni/       # Musical workspaces for `Composizioni, Op. 1`. 
│                       # Each `Op-1_No-*/` subdirectory represents one musical
│                       # piece.
│
├── recipes/            # Local conda packages built via `pixi-build` and 
│                       # declared as workspace dependencies. Each subdirectory
│                       # represents one local conda package recipe.
│
├── docs/               # Technical documentation covering workspace dependencies,
│                       # and detailed project structure.
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

## Quick Start

### I. Prerequisites

- [Pixi](https://pixi.sh/latest/) package manager.
- GNU/Linux-based system on `x86_64` architecture.

> **Note:**  
> These prerequisites are not strict requirements but describe the environment used for development. The project can be set up in alternative environments with different package managers, or operating systems if needed.

### II. Setup

1. **Clone the repository**

    ```bash
    git clone git@github.com:Sierra-Arn/audio-forge-opus-one.git
    cd audio-forge-opus-one
    ```

2. **Install dependencies**

    ```bash
    pixi install
    ```

    > **Note:**  
    > 1. MuseScore is built from source during `pixi install`; this can take a considerable amount of time.
    > 2. Many compiler warnings while building MuseScore are expected and can be ignored.

3. **Activate environment**

    ```bash
    pixi shell
    ```

4. **Fetch MuseScore sources from [score-forge-opus-one](https://github.com/Sierra-Arn/score-forge-opus-one)**

    ```bash
    pixi run fetch-mscz-scores
    ```

### III. Build

With the environment activated and the MuseScore sources in place, publication-ready audio files can be rebuilt in the following steps:

1. **Launch MuseScore**

    ```bash
    musescore
    ```

2. **Export each score to FLAC through the MuseScore GUI**

    For each piece under `composizioni/Op-1_No-*/`:

    1. Open `score.mscz`.

        > **Note:**  
        > Opening a score may print many FluidSynth lines of the form  
        > `SoundFont(.../MuseScore_General.sf3) Sample(...) fowled (broken soundfont?), fixing up`  
        > (often for pizzicato samples such as `BassPzz_*`, `CellPzz_*`, `ViolPzz_*`, `VlnsPzz_*`).  
        > These messages are expected and can be ignored if MuseScore opens and plays back without crashing.

    2. Choose **File -> Export**.
    3. Set **Export to** to **FLAC Audio**.
    4. In the **What to export** block:

        - For every piece except *«No. 3: Abyss»* and *«No. 5: To the Beloved»*: check **Full Score** only.
        - For *«No. 3: Abyss»* and *«No. 5: To the Beloved»*: uncheck **Full Score**, and instead check every listed part (for example **Piano**, **Harp**, **Soprano**, **Contralto**).

    5. In the **export options** block, set:

        | Setting | Value |
        |---|---|
        | Normalize | **Off** (unchecked) |
        | Sample rate | **48000 Hz** |

    6. Save the output into the same piece directory.

        > **Note:**  
        > MuseScore names the written files from the **What to export** selection:
        > - If **Full Score** only is checked, it writes a single `score.flac`.
        > - If individual parts are checked instead, it writes one file per part as `score-<Part>.flac`  
        > (for example `score-Piano.flac`, `score-Soprano.flac`).

3. **Close MuseScore**

    Close the application via the window close button in the MuseScore GUI.

4. **Apply send/return reverb for every piece into `reverbed.flac`**

    ```bash
    pixi run reverb-all
    ```

5. **Apply constant gain to `reverbed.flac` into `normalized.flac` for every piece**

    ```bash
    pixi run normalize-loudness-all
    ```

6. **Create `release.flac` from `normalized.flac` with release metadata for every piece**

    ```bash
    pixi run release-all
    ```

> **Want to see what happens under the hood?**  
> The Pixi tasks that drive this pipeline are defined here:
> - [Workspace tasks](./pixi.toml)
>
> Those tasks invoke the audio pipeline CLIs. Every file is fully documented with detailed docstrings:
> - [Pipeline CLIs](./recipes/scripts/src/scripts/)

## License

Every file in this project is licensed under the [Apache License, Version 2.0](LICENSE-APACHE-2.0).

The MuseScore sources (`.mscz`) are obtained from [score-forge-opus-one](https://github.com/Sierra-Arn/score-forge-opus-one) and are licensed under the [Creative Commons Attribution 4.0 International License](LICENSE-CC-BY-4.0). Under that upstream license, all files generated from the `.mscz` files and all files further derived from those outputs — including audio produced in this workspace — are also licensed under the [Creative Commons Attribution 4.0 International License](LICENSE-CC-BY-4.0).
