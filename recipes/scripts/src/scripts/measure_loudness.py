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

# recipes/scripts/src/scripts/measure_loudness.py
import argparse
import re
import subprocess
import sys
from pathlib import Path

# YouTube-oriented reference points
_REF_I = -14.0
_REF_TP = -1.0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments for measure-loudness.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing flac.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Measure EBU R128 I, TP, and LRA of one FLAC file, and recommend "
            "a constant gain that preserves dynamics for classical material."
        ),
    )
    parser.add_argument(
        "flac",
        type=Path,
        help="Path to a FLAC file.",
    )
    return parser.parse_args(argv)


def _parse_ebur128_summary(stderr: str) -> tuple[float, float, float]:
    """
    Extract I, LRA, and true peak from ffmpeg ebur128 stderr.

    Parameters
    ----------
    stderr : str
        Captured ffmpeg stderr text.

    Returns
    -------
    tuple of float
        (integrated loudness in LUFS, loudness range in LU, true peak in dBTP).

    Raises
    ------
    RuntimeError
        If a required measurement is missing or not numeric.
    """
    integrated_match = re.search(
        r"Integrated loudness:\s*\n\s*I:\s*([-+]?\d+(?:\.\d+)?)\s*LUFS",
        stderr,
    )
    lra_match = re.search(
        r"Loudness range:\s*\n\s*LRA:\s*([-+]?\d+(?:\.\d+)?)\s*LU",
        stderr,
    )
    true_peak_match = re.search(
        r"True peak:\s*\n\s*Peak:\s*([-+]?\d+(?:\.\d+)?)\s*dBFS",
        stderr,
    )
    if integrated_match is None:
        raise RuntimeError(
            "ffmpeg ebur128 did not print an integrated loudness summary"
        )
    if lra_match is None:
        raise RuntimeError(
            "ffmpeg ebur128 did not print a loudness range summary"
        )
    if true_peak_match is None:
        raise RuntimeError(
            "ffmpeg ebur128 did not print a true peak summary"
        )

    try:
        return (
            float(integrated_match.group(1)),
            float(lra_match.group(1)),
            float(true_peak_match.group(1)),
        )
    except ValueError as exc:
        raise RuntimeError(
            "ffmpeg ebur128 summary contained a non-numeric measurement"
        ) from exc


def measure_flac(source_path: Path) -> dict[str, float | bool | str]:
    """
    Measure loudness of one FLAC and constant-gain feasibility.

    Parameters
    ----------
    source_path : Path
        Path to the FLAC file.

    Returns
    -------
    dict of str to float or bool or str
        Meter readings and gain recommendation.

    Raises
    ------
    FileNotFoundError
        If the FLAC file is missing.
    ValueError
        If the path is not a .flac file.
    RuntimeError
        If ffmpeg fails or measurements cannot be parsed.
    """
    path = source_path.expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"FLAC not found: {path}")
    if path.suffix.lower() != ".flac":
        raise ValueError(f"expected a .flac file: {path}")

    absolute = path.resolve()
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(absolute),
            "-af",
            "ebur128=peak=true:framelog=quiet",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        integrated, lra, true_peak = _parse_ebur128_summary(
            completed.stderr or ""
        )
    except RuntimeError:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            f"ffmpeg ebur128 measure failed for {absolute}{suffix}"
        )

    gain_to_i = _REF_I - integrated
    peak_after_i_gain = true_peak + gain_to_i
    gain_to_tp = _REF_TP - true_peak
    i_after_tp_gain = integrated + gain_to_tp
    both_ok = peak_after_i_gain <= _REF_TP
    recommended_gain = gain_to_i if both_ok else gain_to_tp
    recommended_i = integrated + recommended_gain

    return {
        "path": str(absolute),
        "i": integrated,
        "tp": true_peak,
        "lra": lra,
        "gain_to_i": gain_to_i,
        "peak_after_i_gain": peak_after_i_gain,
        "gain_to_tp": gain_to_tp,
        "i_after_tp_gain": i_after_tp_gain,
        "both_ok": both_ok,
        "recommended_gain": recommended_gain,
        "recommended_i": recommended_i,
    }


def _print_report(report: dict[str, float | bool | str]) -> None:
    """
    Print one FLAC measurement report to stdout.

    Parameters
    ----------
    report : dict of str to float or bool or str
        Output of measure_flac.
    """
    both_ok = bool(report["both_ok"])
    mode = "linear" if both_ok else "dynamic"
    print(report["path"])
    print(
        f"  I={report['i']:.2f} LUFS  "
        f"TP={report['tp']:.2f} dBTP  "
        f"LRA={report['lra']:.2f} LU"
    )
    print(
        f"  to reach I={_REF_I:g}: need gain {report['gain_to_i']:+.2f} dB, "
        f"then peak would be {report['peak_after_i_gain']:+.2f} dBTP"
    )
    print(
        f"  to reach TP={_REF_TP:g}: need gain {report['gain_to_tp']:+.2f} dB, "
        f"then I would be {report['i_after_tp_gain']:.2f} LUFS"
    )
    print(f"  normalize-loudness I={_REF_I:g} TP={_REF_TP:g}: {mode}")
    print(
        "  Classical material prioritizes dynamics and spectrum over a strict "
        f"I={_REF_I:g} match."
    )
    print(
        "  Recommended: "
        f"normalize-loudness <piece-dir> "
        f"--gain={report['recommended_gain']:.2f} "
        f"(I ≈ {report['recommended_i']:.2f} LUFS at TP≤{_REF_TP:g})."
    )


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point for measure-loudness.

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
        report = measure_flac(args.flac)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "example: measure-loudness "
            "composizioni/Op-1_No-1_Believe/score.flac",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
