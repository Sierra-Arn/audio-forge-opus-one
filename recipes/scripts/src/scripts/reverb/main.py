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

# recipes/scripts/src/scripts/reverb/main.py
import argparse
import sys
from scripts.reverb.domain import OUTPUT_NAME, PROGRAM
from scripts.reverb.no3 import PIECE_DIR as NO3_DIR
from scripts.reverb.no3 import reverb_no3
from scripts.reverb.no5 import PIECE_DIR as NO5_DIR
from scripts.reverb.no5 import reverb_no5
from scripts.reverb.single import reverb_single


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments for reverb.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing piece_dir, optional send, and optional
        per-stem send flags.
    """
    parser = argparse.ArgumentParser(
        description=(
            f"Apply DuskVerb {PROGRAM} as a send/return and write "
            f"composizioni/<piece-dir>/{OUTPUT_NAME}. One-instrument pieces "
            f"take a positional send; {NO3_DIR} and {NO5_DIR} take per-stem "
            "send flags."
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
        "send",
        nargs="?",
        type=float,
        default=None,
        help=(
            "Linear send level k for one-instrument pieces "
            "(dry + k * wet). Ignored for No. 3 and No. 5."
        ),
    )
    parser.add_argument(
        "--send-piano",
        type=float,
        default=None,
        help="Linear send level for the Piano stem (No. 3 and No. 5).",
    )
    parser.add_argument(
        "--send-harp",
        type=float,
        default=None,
        help="Linear send level for the Harp stem (No. 3).",
    )
    parser.add_argument(
        "--send-soprano",
        type=float,
        default=None,
        help="Linear send level for the Soprano stem (No. 3 and No. 5).",
    )
    parser.add_argument(
        "--send-contralto",
        type=float,
        default=None,
        help="Linear send level for the Contralto stem (No. 5).",
    )
    return parser.parse_args(argv)


def _require_stem_sends(
    label: str,
    required: dict[str, float | None],
) -> dict[str, float]:
    """
    Require that every listed per-stem send flag was provided.

    Parameters
    ----------
    label : str
        Piece directory name for error text.
    required : dict of str to float or None
        Mapping of stem label to parsed send value.

    Returns
    -------
    dict of str to float
        The same mapping with all values present.

    Raises
    ------
    ValueError
        If any required send is missing.
    """
    missing = [name for name, value in required.items() if value is None]
    if missing:
        flags = ", ".join(f"--send-{name.lower()}" for name in missing)
        raise ValueError(f"{label} requires {flags}")
    return {name: float(value) for name, value in required.items()}


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point for reverb.

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
        if args.piece_dir == NO3_DIR:
            sends = _require_stem_sends(
                NO3_DIR,
                {
                    "Piano": args.send_piano,
                    "Harp": args.send_harp,
                    "Soprano": args.send_soprano,
                },
            )
            reverb_no3(
                sends["Piano"],
                sends["Harp"],
                sends["Soprano"],
            )
        elif args.piece_dir == NO5_DIR:
            sends = _require_stem_sends(
                NO5_DIR,
                {
                    "Piano": args.send_piano,
                    "Soprano": args.send_soprano,
                    "Contralto": args.send_contralto,
                },
            )
            reverb_no5(
                sends["Piano"],
                sends["Soprano"],
                sends["Contralto"],
            )
        else:
            if args.send is None:
                raise ValueError(
                    "one-instrument pieces require a send level, "
                    "e.g. reverb Op-1_No-1_Believe 0.2"
                )
            # Per-stem flags are ignored for one-instrument pieces.
            reverb_single(args.piece_dir, args.send)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "example: reverb Op-1_No-1_Believe 0.2",
            file=sys.stderr,
        )
        print(
            "example: reverb Op-1_No-3_Abyss "
            "--send-piano 0.2 --send-harp 0.15 --send-soprano 0.3",
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
