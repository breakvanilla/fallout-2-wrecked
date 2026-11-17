#!/bin/sh
# Builds the mod. usage: ./build.sh [mac] [windows] [test] [-DNAME=value ...]
# mac: local/build-universal (Apple Silicon and Intel); windows: local/build-windows (cross-compiled
# with mingw-w64); test: local/build-test (the hidden test run hooks). No target means mac and windows.
# Arguments starting with -D go to CMake. JOBS sets the parallel jobs (default 8).
set -eu

MOD_SRC="$(cd "$(dirname "$0")" && pwd)"
ENGINE="$MOD_SRC/local/engine"
F2CE_REV=e97087b9582f37075db347a89898887320753f8b

targets=""
cmake_args=""
for arg in "$@"; do
	case "$arg" in
		-D*) cmake_args="$cmake_args $arg" ;;
		mac|windows|test) targets="$targets $arg" ;;
		*) echo "unknown argument: $arg" >&2; exit 1 ;;
	esac
done
[ -n "$targets" ] || targets="mac windows"

# local/engine/ is upstream fallout2-ce at F2CE_REV with patches/ on top
if [ ! -d "$ENGINE/.git" ]; then
	git clone https://github.com/alexbatalov/fallout2-ce "$ENGINE"
	git -C "$ENGINE" checkout -q "$F2CE_REV"
	git -C "$ENGINE" apply -q --3way "$MOD_SRC"/patches/*.patch
fi
"$MOD_SRC/tools/update-patches.sh" --check || echo "Note: local/engine/ has changes not in patches/ yet, run tools/update-patches.sh"

for target in $targets; do
	case "$target" in
		mac)
			dir="$MOD_SRC/local/build-universal"
			# shellcheck disable=SC2086
			cmake -S "$ENGINE" -B "$dir" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64" \
				-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DCMAKE_POLICY_VERSION_MINIMUM=3.5 $cmake_args > /dev/null
			;;
		windows)
			dir="$MOD_SRC/local/build-windows"
			# one exe that needs only Windows' own DLLs
			# shellcheck disable=SC2086
			cmake -S "$ENGINE" -B "$dir" -DCMAKE_TOOLCHAIN_FILE="$MOD_SRC/cmake/mingw-w64-x86_64.cmake" \
				-DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 $cmake_args > /dev/null
			;;
		test)
			dir="$MOD_SRC/local/build-test"
			# shellcheck disable=SC2086
			cmake -S "$ENGINE" -B "$dir" -DWRECKED_TEST=ON -DCMAKE_BUILD_TYPE=Release \
				-DCMAKE_POLICY_VERSION_MINIMUM=3.5 $cmake_args > /dev/null
			;;
	esac
	cmake --build "$dir" -j "${JOBS:-8}"
done
