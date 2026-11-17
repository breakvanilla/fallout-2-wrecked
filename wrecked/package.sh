#!/bin/zsh
# Makes the player zips in local/dist/ from the release builds in
# local/build-universal and local/build-windows (./build.sh).
set -e
REPO="${0:A:h:h}"
DIST="$REPO/local/dist"
APP="$REPO/local/build-universal/Wrecked Fallout 2.app"
EXE="$REPO/local/build-windows/Wrecked Fallout 2.exe"
DEPS="$REPO/local/build-universal/_deps"
MINGW_COPYING="${MINGW_COPYING:-$(brew --prefix mingw-w64)/COPYING}"
for binary in "$APP/Contents/MacOS/Wrecked Fallout 2" "$EXE"; do
  if strings -a "$binary" | grep -q -E 'WRECKED_TEST|DESTRUCT_TEST'; then
    echo "test build, not packaged: $binary"
    exit 1
  fi
done
for file in "$DEPS/sdl2-src/LICENSE.txt" "$DEPS/zlib-src/LICENSE" "$DEPS/fpattern-src/LICENSE" "$MINGW_COPYING"; do
  [ -f "$file" ] || { echo "missing licence: $file"; exit 1; }
done
command rm -rf "$DIST"
for platform in mac windows; do
  STAGE="$DIST/stage-$platform"
  mkdir -p "$STAGE/wrecked-fallout-2/LICENSES"
  cp "$REPO/wrecked/wrecked-fallout-2/sprites.dat" "$REPO/wrecked/wrecked-fallout-2/wrecked.ini" "$STAGE/wrecked-fallout-2/"
  cp "$REPO/wrecked/package/README.txt" "$STAGE/"
  cp "$REPO/LICENSE.md" "$STAGE/LICENSE-fallout2-ce.md"
  # The libraries linked into the program.
  cp "$DEPS/sdl2-src/LICENSE.txt" "$STAGE/wrecked-fallout-2/LICENSES/SDL2.txt"
  cp "$DEPS/zlib-src/LICENSE" "$STAGE/wrecked-fallout-2/LICENSES/zlib.txt"
  cp "$DEPS/fpattern-src/LICENSE" "$STAGE/wrecked-fallout-2/LICENSES/fpattern.txt"
done
cp "$MINGW_COPYING" "$DIST/stage-windows/wrecked-fallout-2/LICENSES/mingw-w64.txt"
ditto "$APP" "$DIST/stage-mac/Wrecked Fallout 2.app"
# Not signed by Apple; an ad-hoc signature at least keeps the bundle whole.
codesign --force --deep --sign - "$DIST/stage-mac/Wrecked Fallout 2.app"
x86_64-w64-mingw32-strip -o "$DIST/stage-windows/Wrecked Fallout 2.exe" "$EXE"
# Windows readers want CRLF line ends.
(cd "$DIST/stage-windows" && perl -pi -e 's/\r?\n/\r\n/' README.txt LICENSE-fallout2-ce.md wrecked-fallout-2/wrecked.ini wrecked-fallout-2/LICENSES/*.txt)
(cd "$DIST/stage-mac" && ditto -c -k --norsrc . "$DIST/wrecked-fallout-2-mac.zip")
(cd "$DIST/stage-windows" && zip -qr -X "$DIST/wrecked-fallout-2-windows.zip" .)
command rm -rf "$DIST/stage-mac" "$DIST/stage-windows"
ls -la "$DIST"
