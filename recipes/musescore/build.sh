#!/usr/bin/env bash

# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# recipes/musescore/build.sh
set -euxo pipefail

# ==================================================================================================

# MuseScore build can cause OOM.
# If CPU_COUNT is unset, cap parallel jobs to nproc/4 (minimum 1)
_cores="${CPU_COUNT:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}"
_jobs=$((_cores / 4))
if [ "${_jobs}" -lt 1 ]; then
    _jobs=1
fi

export CPU_COUNT="${_jobs}"
export CMAKE_BUILD_PARALLEL_LEVEL="${_jobs}"
export MAKEFLAGS="-j${_jobs}"
export NINJAFLAGS="-j${_jobs}"

export PATH="${PREFIX}/bin:${PATH}"
export CMAKE_PREFIX_PATH="${PREFIX}"
export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="${PREFIX}/lib:${LD_LIBRARY_PATH:-}"

# ==================================================================================================
# Stage MuseScore General HQ from the recipe's musfe/ sources into share/sound/ so CMake installs
# it as the default MuseScore_General.sf3 (instead of the FluidR3Mono placeholder).
# ==================================================================================================

_sound_dir="$(pwd)/share/sound"
_muxt="$(pwd)/musfe/MUSFE.muxt"
_sf3_sha256="59808788ee5d6e1b908f2b5ec717aba529c96973903c68139a35835f6db8d511"

mkdir -p "${_sound_dir}"
unzip -o -j "${_muxt}" "soundfonts/MuseScore_General_HQ.sf3" -d "${_sound_dir}"
echo "${_sf3_sha256}  ${_sound_dir}/MuseScore_General_HQ.sf3" | sha256sum -c -
cp -f "${_sound_dir}/MuseScore_General_HQ.sf3" "${_sound_dir}/MuseScore_General.sf3"
# License: share/sound/CMakeLists.txt falls back to FluidR3Mono_License.md.

# ==================================================================================================

mkdir -p build.release
cd build.release

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${PREFIX}" \
    -DCMAKE_PREFIX_PATH="${PREFIX}" \
    -DMSCORE_INSTALL_SUFFIX="" \
    -DMUSESCORE_BUILD_CONFIG=release \
    -DMUSESCORE_REVISION="$(git -C .. rev-parse --short=7 HEAD)" \
    -DBUILD_LAME=ON \
    -DBUILD_PULSEAUDIO=ON \
    -DBUILD_PORTAUDIO=ON \
    -DBUILD_PORTMIDI=ON \
    -DBUILD_ALSA=ON \
    -DBUILD_JACK=OFF \
    -DBUILD_WEBENGINE=OFF \
    -DUSE_SYSTEM_FREETYPE=ON \
    -DDOWNLOAD_SOUNDFONT=OFF \
    -DUSE_ZITA_REVERB=ON \
    -DCMAKE_SKIP_RPATH=OFF

cmake --build . --target lrelease --parallel "${CPU_COUNT}"
cmake --build . --parallel "${CPU_COUNT}"
cmake --install . --strip

# CMake only installs MuseScore_General.sf3; also ship the HQ filename.
_sound_install="$(find "${PREFIX}/share" -type d -name 'sound' -print -quit)"
cp -f ../share/sound/MuseScore_General_HQ.sf3 \
    "${_sound_install}/MuseScore_General_HQ.sf3"

# ==================================================================================================

ln -sfn mscore "${PREFIX}/bin/musescore"
ln -sfn mscore "${PREFIX}/bin/musescore3"

# ==================================================================================================
