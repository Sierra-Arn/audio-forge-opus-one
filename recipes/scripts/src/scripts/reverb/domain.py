# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# recipes/scripts/src/scripts/reverb/domain.py
import subprocess
import sys
import tempfile
from pathlib import Path

OUTPUT_NAME = "reverbed.flac"
_WET_SUFFIX = "-wet.wav"
_PLUGIN_RELATIVE = Path("lib") / "vst3" / "DuskVerb.vst3"
PROGRAM = "Bright Hall"


def validate_send(send: float) -> float:
    """
    Require a non-negative finite linear send level.

    Parameters
    ----------
    send : float
        Candidate send level k.

    Returns
    -------
    float
        The same send value.

    Raises
    ------
    ValueError
        If send is NaN or negative.
    """
    if send != send or send < 0.0:
        raise ValueError(f"send must be a non-negative finite number: {send}")
    return send


def plugin_path() -> Path:
    """
    Resolve the DuskVerb VST3 path inside the active conda/pixi prefix.

    Returns
    -------
    Path
        Absolute path to DuskVerb.vst3.

    Raises
    ------
    FileNotFoundError
        If the plugin is missing from sys.prefix.
    """
    path = Path(sys.prefix) / _PLUGIN_RELATIVE
    if not path.exists():
        raise FileNotFoundError(f"DuskVerb.vst3 not found: {path}")
    return path


def stem_path(piece_path: Path, part: str | None = None) -> Path:
    """
    Build the dry stem path under composizioni/<piece>/.

    Parameters
    ----------
    piece_path : Path
        Absolute path to the piece directory.
    part : str or None, optional
        Part name for multi-stem pieces (e.g. Piano). If None, use score.flac.
        Default is None.

    Returns
    -------
    Path
        Absolute path to the dry FLAC stem.
    """
    if part is None:
        return piece_path / "score.flac"
    return piece_path / f"score-{part}.flac"


def require_stems(piece_path: Path, parts: tuple[str, ...] | None = None) -> list[Path]:
    """
    Resolve dry stem paths and require that each file exists.

    Parameters
    ----------
    piece_path : Path
        Absolute path to the piece directory.
    parts : tuple of str or None, optional
        Part names for multi-stem pieces. If None, require score.flac.
        Default is None.

    Returns
    -------
    list of Path
        Absolute paths to the dry stems, in the same order as parts (or one
        score path when parts is None).

    Raises
    ------
    FileNotFoundError
        If any required stem is missing.
    """
    if parts is None:
        paths = [stem_path(piece_path)]
    else:
        paths = [stem_path(piece_path, part) for part in parts]

    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"{path.name} not found: {path}")
    return paths


def render_wet(source_path: Path, wet_path: Path) -> None:
    """
    Render a 100% wet Bright Hall stem with Plugalyzer (Bus Mode On).

    Parameters
    ----------
    source_path : Path
        Absolute path to the dry stem.
    wet_path : Path
        Absolute path for the temporary wet WAV.

    Raises
    ------
    RuntimeError
        If plugalyzer exits non-zero.
    """
    completed = subprocess.run(
        [
            "plugalyzer",
            "process",
            "--plugin",
            str(plugin_path()),
            "--input",
            str(source_path),
            "--output",
            str(wet_path),
            "--overwrite",
            "--param",
            f"Program:{PROGRAM}",
            "--param",
            "Bus Mode:On",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            f"plugalyzer process failed for {source_path}{suffix}"
        )


def mix_weighted(
    layers: list[tuple[Path, float]],
    output_path: Path,
    balances: list[float] | None = None,
) -> None:
    """
    Sum weighted audio layers into a FLAC via ffmpeg amix.

    Parameters
    ----------
    layers : list of (Path, float)
        Absolute input paths with linear weights. Empty list is invalid.
    output_path : Path
        Absolute path for the mixed FLAC.
    balances : list of float or None, optional
        Stereo balance per layer in [-1, 1] (negative = left). If None,
        leave each layer centered. Default is None.

    Raises
    ------
    ValueError
        If layers is empty or balances length mismatches.
    RuntimeError
        If ffmpeg exits non-zero.
    """
    if not layers:
        raise ValueError("mix_weighted requires at least one layer")

    n = len(layers)
    if balances is None:
        balances = [0.0] * n
    if len(balances) != n:
        raise ValueError(
            "layers and balances must have the same length: "
            f"{n} != {len(balances)}"
        )

    weights = " ".join(f"{weight:g}" for _, weight in layers)
    # normalize=0 keeps a true sum (send/return model).
    # duration=longest keeps reverb tails past the dry ends.
    balance_filters: list[str] = []
    amix_labels: list[str] = []
    for index, balance in enumerate(balances):
        if abs(balance) < 1e-12:
            amix_labels.append(f"[{index}:a]")
            continue
        label = f"b{index}"
        balance_filters.append(
            f"[{index}:a]stereotools=balance_out={balance:g}[{label}]"
            if balance >= 0
            else f"[{index}:a]stereotools=balance_out=\\{balance:g}[{label}]"
        )
        amix_labels.append(f"[{label}]")

    amix = (
        "".join(amix_labels)
        + f"amix=inputs={n}:duration=longest:dropout_transition=0:"
        f"weights={weights}:normalize=0"
    )
    filtergraph = (
        ";".join(balance_filters + [amix]) if balance_filters else amix
    )

    argv = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
    ]
    for path, _ in layers:
        argv.extend(["-i", str(path)])
    argv.extend(
        [
            "-filter_complex",
            filtergraph,
            "-c:a",
            "flac",
            str(output_path),
        ]
    )

    completed = subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"ffmpeg amix failed{suffix}")


def reverb_stems(
    dry_paths: list[Path],
    sends: list[float],
    output_path: Path,
    pans: list[float] | None = None,
) -> Path:
    """
    Apply per-stem send/return reverb and write one mixed FLAC.

    For each dry stem i, Plugalyzer renders wet_i at Bus Mode. The output is:

        sum_i(dry_i) + sum_i(send_i * wet_i)

    Optional per-stem pans shift dry_i and wet_i by the same balance so the
    reverb image follows the dry stem.

    Parameters
    ----------
    dry_paths : list of Path
        Absolute dry stem paths.
    sends : list of float
        Linear send level per stem. Must match dry_paths length.
    output_path : Path
        Absolute path for the written reverbed FLAC.
    pans : list of float or None, optional
        Stereo balance per stem in [-1, 1] (negative = left). If None,
        leave every stem centered. Default is None.

    Returns
    -------
    Path
        Absolute path of the written reverbed FLAC.

    Raises
    ------
    ValueError
        If lengths differ or a send is invalid.
    RuntimeError
        If plugalyzer or ffmpeg fails.
    """
    if len(dry_paths) != len(sends):
        raise ValueError(
            "dry_paths and sends must have the same length: "
            f"{len(dry_paths)} != {len(sends)}"
        )
    if pans is None:
        pans = [0.0] * len(dry_paths)
    if len(pans) != len(dry_paths):
        raise ValueError(
            "dry_paths and pans must have the same length: "
            f"{len(dry_paths)} != {len(pans)}"
        )
    sends = [validate_send(send) for send in sends]

    with tempfile.TemporaryDirectory(prefix="reverb-") as tmp_dir:
        tmp = Path(tmp_dir)
        wet_paths: list[Path] = []
        for index, dry_path in enumerate(dry_paths):
            wet_path = tmp / f"{index}{_WET_SUFFIX}"
            render_wet(dry_path, wet_path)
            wet_paths.append(wet_path)

        layers: list[tuple[Path, float]] = [
            (dry_path, 1.0) for dry_path in dry_paths
        ]
        layers.extend(
            (wet_path, send) for wet_path, send in zip(wet_paths, sends)
        )
        # Dry and wet of the same stem share one pan.
        balances = list(pans) + list(pans)
        mix_weighted(layers, output_path, balances=balances)

    return output_path
