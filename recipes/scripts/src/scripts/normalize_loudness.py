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

# recipes/scripts/src/scripts/normalize_loudness.py
import argparse
import subprocess
import sys
from pathlib import Path
from scripts.paths import find_project_root, resolve_piece_path

_SOURCE_NAME = "reverbed.flac"
_OUTPUT_NAME = "normalized.flac"
_SAMPLE_RATE = 48000


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments for normalize-loudness.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing piece_dir and gain.
    """
    parser = argparse.ArgumentParser(
        description=(
            f"Apply a constant gain to composizioni/<piece-dir>/{_SOURCE_NAME} "
            f"and write {_OUTPUT_NAME}. Pass --gain from measure-loudness."
        ),
    )
    parser.add_argument(
        "piece_dir",
        help=(
            "Directory name under composizioni/, "
            "e.g. Op-1_No-1_Believe."
        ),
    )
    parser.add_argument(
        "--gain",
        type=float,
        required=True,
        help=(
            "Constant gain in dB from measure-loudness "
            "(e.g. --gain=6.7)."
        ),
    )
    return parser.parse_args(argv)


def _apply_gain(source_path: Path, output_path: Path, gain_db: float) -> None:
    """
    Apply a constant gain with ffmpeg and write a FLAC.

    Parameters
    ----------
    source_path : Path
        Absolute path to the input FLAC.
    output_path : Path
        Absolute path for the output FLAC.
    gain_db : float
        Constant gain in dB.

    Raises
    ------
    RuntimeError
        If ffmpeg fails.
    """
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "error",
            "-i",
            str(source_path),
            "-af",
            f"volume={gain_db:g}dB",
            "-ar",
            str(_SAMPLE_RATE),
            "-c:a",
            "flac",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            f"ffmpeg volume failed for {source_path}{suffix}"
        )


def normalize_loudness(piece_dir: str, gain_db: float) -> Path:
    """
    Apply a constant gain to one piece's reverbed FLAC.

    Parameters
    ----------
    piece_dir : str
        Directory name under composizioni/.
    gain_db : float
        Constant gain in dB (from measure-loudness).

    Returns
    -------
    Path
        Absolute path of the written normalized FLAC.

    Raises
    ------
    ValueError
        If piece_dir is not a bare directory name.
    FileNotFoundError
        If the project root, piece directory, or source FLAC is missing.
    RuntimeError
        If ffmpeg fails.
    """
    project_root = find_project_root()
    piece_path = resolve_piece_path(piece_dir, project_root=project_root)
    source_path = piece_path / _SOURCE_NAME
    output_path = piece_path / _OUTPUT_NAME

    if not source_path.is_file():
        raise FileNotFoundError(f"{_SOURCE_NAME} not found: {source_path}")

    _apply_gain(source_path, output_path, gain_db)
    return output_path


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point for normalize-loudness.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    int
        Process exit code. Zero on success, one on failure.
    """
    args = _parse_args(argv)
    try:
        normalize_loudness(args.piece_dir, args.gain)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "example: normalize-loudness Op-1_No-1_Believe --gain=6.7",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
