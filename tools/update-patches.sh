#!/bin/sh
# Writes the changes made in local/engine/ back into patches/, one patch per part of the mod.
# With --check, only reports whether patches/ is out of date (exit 1).
set -eu

MOD_SRC="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$MOD_SRC/local/engine"
REV="$(sed -n 's/^F2CE_REV=//p' "$MOD_SRC/build.sh")"
TMP="$(mktemp -d /tmp/wrecked-f2-patches.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/patches"
mkdir "$OUT"

# file name and the engine paths it covers
PARTS="
01-build:CMakeLists.txt os
02-destruct:src/destruct.cc src/destruct.h
03-game-hooks:src/actions.cc src/animation.cc src/animation.h src/audio_engine.cc src/cache.cc src/combat.cc src/combat.h src/game.cc src/loadsave.cc src/loadsave.h src/map.cc src/object.cc src/sound_effects_cache.h src/svga.cc src/tile.cc src/tile.h
04-input-and-platform:src/dinput.cc src/input.cc src/win32.cc src/file_find.cc
05-test-runs:src/main.cc
"

# new files show up in the diff only once git knows about them; a copy of the index keeps local/engine/'s own untouched
cp "$ENGINE/.git/index" "$TMP/index"
export GIT_INDEX_FILE="$TMP/index"
git -C "$ENGINE" add --intent-to-add .
diff_engine() {
	git -C "$ENGINE" -c core.quotepath=off -c diff.noprefix=false -c diff.mnemonicPrefix=false \
		diff --no-color --no-ext-diff --no-renames --full-index "$REV" -- "$@"
}

echo "$PARTS" | while IFS=: read -r name paths; do
	[ -n "$name" ] || continue
	# shellcheck disable=SC2086
	diff_engine $paths > "$OUT/$name.patch"
	[ -s "$OUT/$name.patch" ] || rm -f "$OUT/$name.patch"
done
covered="$(echo "$PARTS" | cut -s -d: -f2)"
# shellcheck disable=SC2086
stray="$(git -C "$ENGINE" diff --name-only "$REV" -- . $(for p in $covered; do printf ':!%s ' "$p"; done))"
if [ -n "$stray" ]; then
	echo "Changed files outside every patch group, add them to PARTS in $0:" >&2
	echo "$stray" >&2
	exit 1
fi

if [ "${1:-}" = "--check" ]; then
	diff -r -q "$MOD_SRC/patches" "$OUT" > /dev/null
	exit
fi
mkdir -p "$MOD_SRC/patches"
rm -f "$MOD_SRC"/patches/*.patch
cp "$OUT"/*.patch "$MOD_SRC/patches/"
ls -l "$MOD_SRC"/patches/*.patch
