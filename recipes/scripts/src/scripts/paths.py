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

# recipes/scripts/src/scripts/paths.py
import os
import tomllib
from pathlib import Path
from typing import Any


def find_project_root(start: Path | None = None) -> Path:
    """
    Resolve the workspace root that contains pixi.toml.

    Prefers the PIXI_PROJECT_ROOT environment variable when that directory
    contains pixi.toml. Otherwise walks from start, or the current working
    directory, toward the filesystem root.

    Parameters
    ----------
    start : Path or None, optional
        Directory to begin the ancestor search. If None, Path.cwd() is used.
        Default is None.

    Returns
    -------
    Path
        Absolute path to the project root.

    Raises
    ------
    FileNotFoundError
        If no directory with pixi.toml is found.
    """
    env_root = os.environ.get("PIXI_PROJECT_ROOT")
    if env_root:
        candidate = Path(env_root)
        if (candidate / "pixi.toml").is_file():
            return candidate.resolve()

    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / "pixi.toml").is_file():
            return directory

    raise FileNotFoundError(
        "project root not found (set PIXI_PROJECT_ROOT or run inside the repo)"
    )


def resolve_piece_path(piece_dir: str, project_root: Path | None = None) -> Path:
    """
    Resolve composizioni/<piece-dir> under the project root.

    Parameters
    ----------
    piece_dir : str
        Directory name under composizioni/, for example Op-1_No-1_Believe.
        Must be a bare name, not a path.
    project_root : Path or None, optional
        Project root. If None, find_project_root is used. Default is None.

    Returns
    -------
    Path
        Absolute path to the piece directory.

    Raises
    ------
    ValueError
        If piece_dir contains a path separator.
    FileNotFoundError
        If the project root or piece directory does not exist.
    """
    if "/" in piece_dir:
        raise ValueError(
            "pass the composizioni directory name only, not a path: "
            f"{piece_dir}"
        )

    root = project_root if project_root is not None else find_project_root()
    piece_path = root / "composizioni" / piece_dir
    if not piece_path.is_dir():
        raise FileNotFoundError(f"composizioni directory not found: {piece_path}")
    return piece_path


def load_metadata(project_root: Path | None = None) -> dict[str, Any]:
    """
    Load metadata.toml from the project root.

    Parameters
    ----------
    project_root : Path or None, optional
        Project root. If None, find_project_root is used. Default is None.

    Returns
    -------
    dict of str to Any
        Parsed TOML document.

    Raises
    ------
    FileNotFoundError
        If metadata.toml is missing.
    """
    root = project_root if project_root is not None else find_project_root()
    path = root / "metadata.toml"
    if not path.is_file():
        raise FileNotFoundError(f"metadata.toml not found: {path}")

    with path.open("rb") as handle:
        return tomllib.load(handle)
