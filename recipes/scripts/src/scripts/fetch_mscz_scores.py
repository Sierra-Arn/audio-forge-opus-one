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

# recipes/scripts/src/scripts/fetch_mscz_scores.py
import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path
from scripts.paths import find_project_root

_REPO = "Sierra-Arn/score-forge-opus-one"
_REF = "main"
_SCORE_NAME = "score.mscz"
_RAW_HOST = "https://raw.githubusercontent.com"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments for fetch-mscz-scores.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "For each local composizioni/<piece-dir>/, download matching "
            f"{_SCORE_NAME} from {_REPO}@{_REF} via raw HTTPS. Piece "
            "directory names are taken from this project."
        ),
    )
    return parser.parse_args(argv)


def _score_url(piece_dir: str) -> str:
    """
    Build the raw.githubusercontent.com URL for one score.mscz.

    Parameters
    ----------
    piece_dir : str
        Directory name under composizioni/.

    Returns
    -------
    str
        Absolute HTTPS URL.
    """
    return (
        f"{_RAW_HOST}/{_REPO}/{_REF}/composizioni/{piece_dir}/{_SCORE_NAME}"
    )


def _download_score(url: str, dest: Path) -> None:
    """
    Download one score.mscz over HTTPS and write it to dest.

    Parameters
    ----------
    url : str
        Absolute raw.githubusercontent.com URL.
    dest : Path
        Destination path for the downloaded file.

    Raises
    ------
    FileNotFoundError
        If the remote file returns HTTP 404.
    RuntimeError
        If the download fails for another network or HTTP reason.
    """
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError(f"{_SCORE_NAME} not found: {url}") from exc
        raise RuntimeError(
            f"download failed for {url}: HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"download failed for {url}: {reason}") from exc

    dest.write_bytes(data)


def fetch_mscz_scores(project_root: Path | None = None) -> int:
    """
    Download score.mscz for each local composizioni piece directory.

    Parameters
    ----------
    project_root : Path or None, optional
        This project root. If None, find_project_root is used. Default is None.

    Returns
    -------
    int
        Number of score.mscz files written.

    Raises
    ------
    FileNotFoundError
        If the project root or composizioni directory is missing, or a remote
        score.mscz returns HTTP 404.
    RuntimeError
        If a download fails for a non-404 reason.
    """
    root = project_root if project_root is not None else find_project_root()
    composizioni = root / "composizioni"
    if not composizioni.is_dir():
        raise FileNotFoundError(f"composizioni not found: {composizioni}")

    downloaded = 0
    print(f"source: {_RAW_HOST}/{_REPO}/{_REF}")
    for piece_path in sorted(
        path for path in composizioni.iterdir() if path.is_dir()
    ):
        url = _score_url(piece_path.name)
        dest = piece_path / _SCORE_NAME
        _download_score(url, dest)
        downloaded += 1
        print(f"downloaded: {dest.relative_to(root)}")

    return downloaded


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point for fetch-mscz-scores.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector to parse. If None, sys.argv is used. Default is None.

    Returns
    -------
    int
        Process exit code. Zero on success, one on failure.
    """
    _parse_args(argv)
    try:
        count = fetch_mscz_scores()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"done: {count} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
