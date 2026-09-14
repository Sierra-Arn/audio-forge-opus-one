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

# recipes/scripts/src/scripts/reverb/no5.py
from pathlib import Path
from scripts.paths import find_project_root, resolve_piece_path
from scripts.reverb.domain import OUTPUT_NAME, require_stems, reverb_stems

PIECE_DIR = "Op-1_No-5_To-the-Beloved"
PARTS = ("Piano", "Soprano", "Contralto")
# Narrow stage: Soprano L10, Piano center, Contralto R10.
_STEM_PANS = (0.0, -0.10, 0.10)


def reverb_no5(piano: float, soprano: float, contralto: float) -> Path:
    """
    Apply per-stem send/return DuskVerb for No. 5: To the Beloved.

    Expects score-Piano.flac, score-Soprano.flac, and
    score-Contralto.flac under the piece directory and writes reverbed.flac.
    Applies a fixed narrow balance (Soprano L10, Piano C, Contralto R10).

    Parameters
    ----------
    piano : float
        Linear send level for the Piano stem.
    soprano : float
        Linear send level for the Soprano stem.
    contralto : float
        Linear send level for the Contralto stem.

    Returns
    -------
    Path
        Absolute path of the written reverbed FLAC.

    Raises
    ------
    ValueError
        If a send is invalid.
    FileNotFoundError
        If the project root, piece directory, a stem, or the plugin is missing.
    RuntimeError
        If plugalyzer or ffmpeg fails.
    """
    project_root = find_project_root()
    piece_path = resolve_piece_path(PIECE_DIR, project_root=project_root)
    dry_paths = require_stems(piece_path, PARTS)
    output_path = piece_path / OUTPUT_NAME
    return reverb_stems(
        dry_paths,
        [piano, soprano, contralto],
        output_path,
        pans=list(_STEM_PANS),
    )
