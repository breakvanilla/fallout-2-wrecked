#!/bin/zsh
# Puts a Mac build and a link to wrecked-fallout-2/ into the local game folder.
# BUILD: build folder (default local/build-universal); FALLOUT2_GAME: game
# folder (default local/game/ in the repo).
set -e
REPO="${0:A:h:h}"
GAME="${FALLOUT2_GAME:-$REPO/local/game}"
GAME="${GAME:A}"
APP="$REPO/${BUILD:-local/build-universal}/Wrecked Fallout 2.app"
[ -f "$GAME/master.dat" ] || { echo "no Fallout 2 in $GAME"; exit 1; }
[ -x "$APP/Contents/MacOS/Wrecked Fallout 2" ] || { echo "no build in $APP"; exit 1; }
if strings -a "$APP/Contents/MacOS/Wrecked Fallout 2" | grep -q -E 'WRECKED_TEST|DESTRUCT_TEST'; then
  echo "test build, not installed: $APP"
  exit 1
fi
command rm -rf "$GAME/Wrecked Fallout 2.app"
ditto "$APP" "$GAME/Wrecked Fallout 2.app"
# Relative inside the repo, so that the repo can move.
if [ "$GAME" = "$REPO/local/game" ]; then
  LINK=../../wrecked/wrecked-fallout-2
else
  LINK="$REPO/wrecked/wrecked-fallout-2"
fi
[ -L "$GAME/wrecked-fallout-2" ] || ln -s "$LINK" "$GAME/wrecked-fallout-2"
echo "installed in $GAME"
