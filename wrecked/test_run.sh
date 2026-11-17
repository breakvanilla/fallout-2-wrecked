#!/bin/zsh
# usage: [MAP=x.map] [BUILD=local/build-test] [ARCH=x86_64] test_run.sh NAME [VAR=value...]
# Output in $WRECKED_TEST_DIR/destruct-NAME/ (default ~/Library/Caches/wrecked-fallout-2);
# runs in the test copy from test_game.sh, never in the game you play.
# /tmp/game-display.lock keeps test runs apart from each other and from a game on screen; gives up after 10 minutes.
LOCK=/tmp/game-display.lock
held=0
for i in {1..300}; do mkdir $LOCK 2>/dev/null && { held=1; break; }; sleep 2; done
if [ $held = 0 ]; then
  echo "display lock held by: $(cat $LOCK/owner 2>/dev/null)"
  exit 1
fi
trap 'command rm -rf /tmp/game-display.lock' EXIT
trap 'exit 130' INT TERM
echo "wrecked fallout 2 hidden test ($1)" > $LOCK/owner
REPO="${0:A:h:h}"
TESTS="${WRECKED_TEST_DIR:-$HOME/Library/Caches/wrecked-fallout-2}"
[ -d "$TESTS/game" ] || "$REPO/wrecked/test_game.sh" > /dev/null
APP="$TESTS/game/Wrecked Test.app"
command rm -rf "$APP"; cp -R "$REPO/${BUILD:-local/build-test}/Wrecked Fallout 2.app" "$APP"
OUT="$TESTS/destruct-$1"; command rm -rf $OUT; mkdir -p $OUT
cd "$TESTS"
shift
RUN=(); [ -n "$ARCH" ] && RUN=(arch -$ARCH)
"${RUN[@]}" env "$@" SDL_AUDIODRIVER=dummy WRECKED_TEST_MAP=${MAP:-artemple.map} DESTRUCT_TEST_OUT=$OUT "$APP/Contents/MacOS/Wrecked Fallout 2" > $OUT/log.txt 2>&1 &
pid=$!
for i in {1..100}; do kill -0 $pid 2>/dev/null || break; sleep 1; done
kill -0 $pid 2>/dev/null && { echo TIMEOUT; kill $pid; }
wait $pid; echo "exit=$?"
command rm -rf "$APP"
for f in $OUT/*.bmp(N); do sips -s format png "$f" --out "${f%.bmp}.png" >/dev/null && command rm "$f"; done
grep -E "destruct" $OUT/log.txt | head -80
