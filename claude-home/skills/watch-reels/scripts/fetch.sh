#!/bin/sh
# Download ONE public post, logged out (never cookies), into a work dir; print the files it saved, one per line.
#   sh fetch.sh "<url>" "<work dir>"        sh fetch.sh --delete "<video file>"...
# A reel or video gives video.mp4. An Instagram post (/p/ or /reel/) gives every slide of that one post:
# slideNN.mp4 for a video slide (slideNN.jpg is then its poster), slideNN.jpg alone for a photo slide.
# The post's caption goes to caption.txt.
set -eu
if [ "${1:-}" = "--delete" ]; then
  shift
  for f in "$@"; do
    case "$f" in *.mp4) ;; *) echo "only .mp4 files: $f" >&2; exit 1 ;; esac
    [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
    rm -f -- "$f"; echo "deleted $f"
  done
  exit 0
fi
URL="${1:?usage: fetch.sh <url> <work dir>}"; DIR="${2:?usage: fetch.sh <url> <work dir>}"
case "$URL" in https://*) ;; *) echo "only https links" >&2; exit 1 ;; esac
command -v yt-dlp >/dev/null || { echo "yt-dlp is not installed (see README)" >&2; exit 1; }
mkdir -p "$DIR"
: > "$DIR/caption.txt"   # --print-to-file appends; a rerun must not stack captions
# --ignore-config: no user config can add cookies.
COMMON="--ignore-config --no-cookies --no-cookies-from-browser --restrict-filenames --no-progress"
FMT='bv*[height<=1920]+ba/b'
case "$URL" in
  https://*instagram.com/p/*|https://*instagram.com/reel/*|https://*instagram.com/*/p/*|https://*instagram.com/*/reel/*)
    # One post's slides only (a profile or feed URL never matches here). A photo slide has no video format:
    # --ignore-no-formats-error keeps it and --write-thumbnail saves the photo itself.
    rm -f -- "$DIR"/slide*   # a rerun must not count slides an earlier, failed run left
    # yt-dlp exits 1 on every photo slide ("No video formats found"), so its exit code cannot tell a photo from a
    # failed video: the checks below read the log and the files instead.
    # shellcheck disable=SC2086
    yt-dlp $COMMON --yes-playlist --ignore-no-formats-error --write-thumbnail --convert-thumbnails jpg \
      -f "$FMT" --merge-output-format mp4 --print-to-file description "$DIR/caption-%(playlist_index|1)s.txt" \
      -o "$DIR/slide%(playlist_index|1)02d.%(ext)s" -o "thumbnail:$DIR/slide%(playlist_index|1)02d.%(ext)s" \
      "$URL" >/dev/null 2>"$DIR/fetch.log" || true
    # every slide failed (private post, login wall, rate limit): say why
    ls "$DIR"/slide* >/dev/null 2>&1 || { tail -n 3 "$DIR/fetch.log" >&2; exit 1; }
    # some slides failed (rate limit mid post): fail the post so it is never marked done with slides missing
    if grep '^ERROR' "$DIR/fetch.log" | grep -qv 'No video formats found'; then
      grep '^ERROR' "$DIR/fetch.log" | grep -v 'No video formats found' | tail -n 3 >&2; exit 1
    fi
    for c in "$DIR"/caption-*.txt; do   # one caption file per slide yt-dlp saw
      n=${c##*caption-}; n=${n%.txt}
      ls "$DIR/slide$n".* >/dev/null 2>&1 || ls "$DIR/slide0$n".* >/dev/null 2>&1 || { echo "slide $n has no file" >&2; exit 1; }
    done
    # every slide repeats the post caption: keep slide 1's
    [ -f "$DIR/caption-1.txt" ] && mv -f -- "$DIR/caption-1.txt" "$DIR/caption.txt"
    for f in "$DIR"/caption-*.txt; do [ -e "$f" ] && rm -f -- "$f"; done
    ls "$DIR"/slide* "$DIR"/caption.txt 2>/dev/null
    ;;
  *)
    # shellcheck disable=SC2086
    yt-dlp $COMMON --no-playlist -f "$FMT" --merge-output-format mp4 --print-to-file description "$DIR/caption.txt" \
      -o "$DIR/video.%(ext)s" --print after_move:filepath "$URL"
    ;;
esac
