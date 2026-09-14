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

# recipes/scripts/src/scripts/write_flac_metadata.py
import argparse
import shutil
import sys
from pathlib import Path
from typing import Any
from mutagen.flac import FLAC
from scripts.paths import find_project_root, load_metadata, resolve_piece_path

_SOURCE_NAME = "normalized.flac"
_RELEASE_NAME = "release.flac"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments for write-flac-metadata.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing piece_dir and title.
    """
    parser = argparse.ArgumentParser(
        description=(
            f"Tag composizioni/<piece-dir>/{_SOURCE_NAME} and write "
            f"{_RELEASE_NAME} via mutagen. Release fields other than title "
            "are read from metadata.toml."
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
        "title",
        help='Track title, e.g. "No. 1: Believe".',
    )
    return parser.parse_args(argv)


def _require_str(meta: dict[str, Any], keys: tuple[str, ...]) -> str:
    """
    Read a nested string field from parsed metadata.toml.

    Parameters
    ----------
    meta : dict of str to Any
        Parsed TOML document.
    keys : tuple of str
        Nested key path, for example ("author", "display_name").

    Returns
    -------
    str
        Field value.

    Raises
    ------
    ValueError
        If any key along the path is missing or the leaf is not a string.
    """
    current: Any = meta
    path = ".".join(keys)
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise ValueError(f"metadata.toml missing required field: {path}")
        current = current[key]

    if not isinstance(current, str):
        raise ValueError(f"metadata.toml field must be a string: {path}")
    return current


def _require_int(meta: dict[str, Any], keys: tuple[str, ...]) -> int:
    """
    Read a nested integer field from parsed metadata.toml.

    Parameters
    ----------
    meta : dict of str to Any
        Parsed TOML document.
    keys : tuple of str
        Nested key path, for example ("date", "year").

    Returns
    -------
    int
        Field value.

    Raises
    ------
    ValueError
        If any key along the path is missing or the leaf is not an integer.
    """
    current: Any = meta
    path = ".".join(keys)
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise ValueError(f"metadata.toml missing required field: {path}")
        current = current[key]

    if not isinstance(current, int):
        raise ValueError(f"metadata.toml field must be an integer: {path}")
    return current


def _format_date(meta: dict[str, Any]) -> str:
    """
    Build an ISO date string from metadata.toml [date] for the Vorbis DATE tag.

    Parameters
    ----------
    meta : dict of str to Any
        Parsed TOML document.

    Returns
    -------
    str
        Date in YYYY-MM-DD form.

    Raises
    ------
    ValueError
        If year, month, or day is missing or out of range.
    """
    year = _require_int(meta, ("date", "year"))
    month = _require_int(meta, ("date", "month"))
    day = _require_int(meta, ("date", "day"))

    if not 1 <= month <= 12:
        raise ValueError(f"metadata.toml date.month out of range: {month}")
    if not 1 <= day <= 31:
        raise ValueError(f"metadata.toml date.day out of range: {day}")

    return f"{year:04d}-{month:02d}-{day:02d}"


def write_release_flac(piece_dir: str, title: str) -> Path:
    """
    Copy the normalized FLAC into the release FLAC with Vorbis comment tags.

    Existing tags are cleared. TITLE comes from the CLI argument; ARTIST,
    ALBUM, DATE, and COPYRIGHT are taken from metadata.toml.

    Parameters
    ----------
    piece_dir : str
        Directory name under composizioni/.
    title : str
        Value for the TITLE tag.

    Returns
    -------
    Path
        Absolute path of the written release FLAC.

    Raises
    ------
    ValueError
        If piece_dir is not a bare directory name, or required metadata keys
        are missing.
    FileNotFoundError
        If the project root, piece directory, source FLAC, or metadata.toml is
        missing.
    RuntimeError
        If mutagen cannot open or save the FLAC file.
    """
    project_root = find_project_root()
    piece_path = resolve_piece_path(piece_dir, project_root=project_root)
    source_path = piece_path / _SOURCE_NAME
    release_path = piece_path / _RELEASE_NAME

    if not source_path.is_file():
        raise FileNotFoundError(f"{_SOURCE_NAME} not found: {source_path}")

    meta = load_metadata(project_root)
    artist = _require_str(meta, ("author", "display_name"))
    album = _require_str(meta, ("work", "collection"))
    date = _format_date(meta)
    copyright_notice = _require_str(meta, ("license", "notice"))

    if release_path.exists():
        release_path.unlink()
    shutil.copy2(source_path, release_path)

    audio = FLAC(release_path)
    if audio.tags is None:
        audio.add_tags()
    else:
        audio.clear()
    audio["TITLE"] = title
    audio["ARTIST"] = artist
    audio["ALBUM"] = album
    audio["DATE"] = date
    audio["COPYRIGHT"] = copyright_notice
    try:
        audio.save()
    except Exception as exc:
        raise RuntimeError(f"failed to save FLAC tags: {release_path}") from exc

    return release_path


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point for write-flac-metadata.

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
        write_release_flac(args.piece_dir, args.title)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            'example: write-flac-metadata Op-1_No-1_Believe "No. 1: Believe"',
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
