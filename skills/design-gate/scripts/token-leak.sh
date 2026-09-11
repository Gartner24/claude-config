#!/usr/bin/env bash
# Corpus-wide assertion that the locked direction is actually portable.
#
# A screenshot cannot prove this and a fixture cannot prove this: the claim is
# universal ("no component hardcodes a color, duration or easing"), so it has to be
# counted across every component file that ships. Prints the offenders and the count.
#
#   token-leak.sh <dir> [dir...]     exit 1 if any literal is found outside tokens.css
#                                    exit 2 if it scanned nothing (see below)
set -uo pipefail
[ $# -ge 1 ] || { echo "usage: token-leak.sh <dir> [dir...]" >&2; exit 2; }

for d in "$@"; do
  [ -e "$d" ] || { echo "token leak: NOT RUN - no such path: $d" >&2; exit 2; }
done

PATTERN='#[0-9a-fA-F]{3,8}\b|rgba?\(|oklch\(|oklab\(|hsla?\(|[0-9]+ms\b|cubic-bezier\('
INCLUDE=(--include='*.tsx' --include='*.jsx' --include='*.ts' --include='*.js'
         --include='*.vue' --include='*.svelte' --include='*.astro' --include='*.html'
         --include='*.css' --include='*.scss' --include='*.sass' --include='*.less'
         --include='*.styl' --include='*.pcss' --include='*.blade.php' --include='*.erb'
         --include='*.heex' --include='*.templ' --include='*.twig' --include='*.liquid'
         --include='*.svg' --include='*.mdx')

# An assertion that scopes its own input passes unconditionally when that input is empty.
# This gate used to report "0 - every color resolves through a token" for a typo'd path,
# for an empty tree, and for any stack whose files fell outside the include list. A green
# result on an unexamined corpus is worse than no gate, because it gets recorded as RAN.
SCANNED=$(grep -rl '' "$@" "${INCLUDE[@]}" 2>/dev/null | grep -cv '/node_modules/' || true)
if [ "${SCANNED:-0}" -eq 0 ]; then
  echo "token leak: NOT RUN - matched 0 files under: $*" >&2
  echo "  The include list covers component and stylesheet extensions only." >&2
  echo "  Point it at the directory that actually holds the components." >&2
  exit 2
fi

# The premise of this check is "every literal resolves through a token in tokens.css".
# On a stack whose token layer is NOT CSS - styled-components with a theme.js object,
# Panda, vanilla-extract, a WordPress theme.json - that premise does not hold, and the
# count it prints is meaningless. It reported "319 lines across 387 files" on a
# styled-components repo whose audit covered one styles file: not a finding, not a pass,
# just a grep reading files it was never designed to judge.
TOKENS_CSS=$(grep -rl --include='tokens.css' '' "$@" 2>/dev/null | grep -v '/node_modules/' | head -1)
if [ -z "$TOKENS_CSS" ]; then
  echo "token leak: NOT APPLICABLE - no tokens.css under: $*" >&2
  echo "  This check proves a CSS custom-property token layer is not bypassed. Point it at" >&2
  echo "  the directory holding tokens.css, or - if this stack keeps tokens elsewhere" >&2
  echo "  (theme.js, Panda, vanilla-extract, theme.json) - close the gate row with the" >&2
  echo "  check that actually fits that layer and say which. Do not record this as clean." >&2
  exit 2
fi

# NOTE: no comment filter. The previous version dropped any line matching ': #', which is
# the shape of `color: #ff0000` - the single most common form of the leak this counts. It
# reported 2 for a file holding 3 hex literals. A literal inside a comment is worth
# flagging anyway: it is what the next person copies.
HITS=$(grep -rEn "$PATTERN" "$@" "${INCLUDE[@]}" 2>/dev/null \
  | grep -v '/tokens\.css:' \
  | grep -v '/node_modules/' || true)

COUNT=$(printf '%s' "$HITS" | grep -c . || true)

if [ "$COUNT" -eq 0 ]; then
  echo "token leak: 0 across $SCANNED file(s) - every color, duration and easing resolves through a token."
  exit 0
fi

echo "token leak: $COUNT line(s) carrying literals across $SCANNED scanned file(s), outside tokens.css"
echo "$HITS" | head -40
[ "$COUNT" -gt 40 ] && echo "... and $((COUNT - 40)) more"
echo
echo "A non-zero count means the direction is not portable, whatever the screenshots look"
echo "like. Move each literal into tokens.css and reference it with var()."
exit 1
