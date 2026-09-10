#!/usr/bin/env bash
# Background removal that keeps hair, fur and soft edges.
#
#   bgremove.sh <in> <out.png> [subject]      subject: general|portrait|anime|cod|hard|fast
#   BGREMOVE_DRY=1 bgremove.sh ...            print the command instead of running it
#
# Why the flags are what they are:
#   -m  ALWAYS passed explicitly. rembg's default is bria-rmbg (RMBG-2.0), CC BY-NC 4.0.
#       One forgotten flag turns a client deliverable into a licence problem.
#   -vm ViTMatte. Re-estimates the alpha AND decontaminates internally, so it recovers
#       strands a plain cut chops off flat. Costs ~3s. Do not also pass -dc.
#   -dc used only for hard-edged subjects (bottle, phone, logo) where there is nothing
#       soft to refine, saving the 3s.
#
# First ever run downloads ~1GB of weights. Warm: 17-20s for a 2000px image on CPU.
set -euo pipefail

IN="${1:-}"; OUT="${2:-}"; SUBJECT="${3:-general}"
[ -n "$IN" ] && [ -n "$OUT" ] || { sed -n '2,4p' "$0"; exit 2; }
[ -f "$IN" ] || { echo "no such file: $IN" >&2; exit 1; }

case "$SUBJECT" in
  general)  MODEL=birefnet-general;   REFINE=-vm ;;
  portrait) MODEL=birefnet-portrait;  REFINE=-vm ;;
  anime)    MODEL=isnet-anime;        REFINE=-vm ;;
  cod)      MODEL=birefnet-cod;       REFINE=-vm ;;  # subject and background similar in tone
  hard)     MODEL=birefnet-general;   REFINE=-dc ;;  # bottle, phone, logo - no soft edge
  fast)     MODEL=isnet-general-use;  REFINE=-dc ;;  # ~4s contact-sheet preview
  *) echo "unknown subject '$SUBJECT' - use general|portrait|anime|cod|hard|fast" >&2; exit 2 ;;
esac

CMD=(uv run --no-project --with "rembg[cpu,cli]==2.0.84" rembg i -m "$MODEL" "$REFINE" "$IN" "$OUT")

if [ -n "${BGREMOVE_DRY:-}" ]; then printf '%q ' "${CMD[@]}"; echo; exit 0; fi

echo "cutting with $MODEL $REFINE (first run downloads ~1GB, then 17-20s warm)"
"${CMD[@]}"

echo
echo "Now LOOK at it on magenta - this is the step people skip and it is the whole game:"
echo "  magick $OUT -background magenta -flatten -crop 400x300+X+Y +repage -filter point -resize 300% check.png"
echo "  coloured rim tracing the silhouette -> re-cut with -vm"
echo "  hair or fur cut off flat            -> add -ae 20"
echo "  faint grey wash in the clear area   -> magick $OUT -channel A -level 5%,95% +channel $OUT"
