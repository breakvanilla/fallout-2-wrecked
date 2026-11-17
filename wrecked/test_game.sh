#!/bin/zsh
# Makes the test copy of the game: links to the game's files, with its own
# data/ (saves, map state) and settings. Run again to reset it.
# FALLOUT2_GAME: game folder (default local/game/ in the repo); WRECKED_TEST_DIR:
# where test runs go (default ~/Library/Caches/wrecked-fallout-2).
set -e
REPO="${0:A:h:h}"
GAME="${FALLOUT2_GAME:-$REPO/local/game}"
GAME="${GAME:A}"
TEST="${WRECKED_TEST_DIR:-$HOME/Library/Caches/wrecked-fallout-2}/game"
TEST="${TEST:A}"
[ -f "$GAME/master.dat" ] || { echo "no Fallout 2 in $GAME"; exit 1; }
case "$GAME/" in
  "$TEST"/*) echo "the test copy $TEST would replace the game in $GAME"; exit 1 ;;
esac
command rm -rf "$TEST"
mkdir -p "$TEST"
for item in "$GAME"/*(N); do
  name="${item:t}"
  case "$name" in
    data|fallout2.cfg|f2_res.ini|*.app|*.exe) ;;
    *) ln -s "$item" "$TEST/$name" ;;
  esac
done
cp -R "$GAME/data" "$TEST/data"
cp "$GAME/fallout2.cfg" "$GAME/f2_res.ini" "$TEST/"
sed -i '' -e 's/^WINDOWED=.*/WINDOWED=1/' -e 's/^SCALE_2X=.*/SCALE_2X=0/' -e 's/^SCR_WIDTH=.*/SCR_WIDTH=640/' -e 's/^SCR_HEIGHT=.*/SCR_HEIGHT=480/' "$TEST/f2_res.ini"
echo "$TEST"
