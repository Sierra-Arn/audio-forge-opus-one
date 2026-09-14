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

# recipes/scripts/src/scripts/reverb/single.py
from pathlib import Path
from scripts.paths import find_project_root, resolve_piece_path
from scripts.reverb.domain import OUTPUT_NAME, require_stems, reverb_stems


def reverb_single(piece_dir: str, send: float) -> Path:
    """
    Apply send/return DuskVerb to a one-instrument piece.

    Expects composizioni/<piece-dir>/score.flac and writes
    composizioni/<piece-dir>/reverbed.flac.

    Parameters
    ----------
    piece_dir : str
        Directory name under composizioni/.
    send : float
        Linear send level k for dry + k * wet.

    Returns
    -------
    Path
        Absolute path of the written reverbed FLAC.

    Raises
    ------
    ValueError
        If piece_dir or send is invalid.
    FileNotFoundError
        If the project root, piece directory, score FLAC, or plugin is missing.
    RuntimeError
        If plugalyzer or ffmpeg fails.
    """
    project_root = find_project_root()
    piece_path = resolve_piece_path(piece_dir, project_root=project_root)
    dry_paths = require_stems(piece_path)
    output_path = piece_path / OUTPUT_NAME
    return reverb_stems(dry_paths, [send], output_path)
