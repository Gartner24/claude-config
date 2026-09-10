#!/usr/bin/env bash
# Store and read the Gemini API key from the GNOME keyring instead of a plaintext export.
#
#   gemini-key.sh set     prompt for the key (hidden, never touches shell history)
#   gemini-key.sh get     print it (used by the skill's generation scripts)
#   gemini-key.sh test    prove the key works and image generation is actually billable
#   gemini-key.sh rm      delete it
#
# Why not ~/.zshrc: an exported key is readable by every process you run, lands in
# backups, and gets shoulder-surfed on a shared screen. The keyring is encrypted at rest
# and unlocked with your login. If gnome-keyring is not running this falls back to
# $GEMINI_API_KEY so nothing breaks.
set -euo pipefail
SERVICE=gemini
ATTR=api

have_keyring() { command -v secret-tool >/dev/null && pgrep -x gnome-keyring-d >/dev/null; }

case "${1:-get}" in
  set)
    have_keyring || { echo "no gnome-keyring - export GEMINI_API_KEY in your shell instead" >&2; exit 1; }
    # -p reads from the terminal, so the key never appears in argv or history
    printf 'Paste the Gemini API key (input hidden), then Enter: ' >&2
    read -rs KEY; echo >&2
    [ -n "$KEY" ] || { echo "empty - nothing stored" >&2; exit 1; }
    printf '%s' "$KEY" | secret-tool store --label='Gemini API key' service "$SERVICE" key "$ATTR"
    echo "stored in the keyring. Verify with: gemini-key.sh test" >&2
    ;;

  get)
    if have_keyring && secret-tool lookup service "$SERVICE" key "$ATTR" 2>/dev/null; then :
    elif [ -n "${GEMINI_API_KEY:-}" ]; then printf '%s' "$GEMINI_API_KEY"
    else
      echo "no Gemini key found. Run: bash ~/.claude/skills/assets/scripts/gemini-key.sh set" >&2
      exit 1
    fi
    ;;

  test)
    KEY="$("$0" get)" || exit 1
    # Private scratch dir, removed on exit. Fixed /tmp/gk*.json names were world-readable,
    # left behind mode 0644, and curl -o follows a symlink - a pre-planted link there is an
    # arbitrary-file overwrite running as you.
    TD=$(mktemp -d); trap 'rm -rf "$TD"' EXIT
    # The key goes in a curl config file on stdin, never in argv: every user on the host
    # can read another process's argv via ps, which would defeat the whole point of the
    # keyring this script exists to use.
    printf 'header = "x-goog-api-key: %s"\n' "$KEY" > "$TD/curlrc"
    echo "1/2 key accepted by the API?"
    code=$(curl -s -K "$TD/curlrc" -o "$TD/gk.json" -w '%{http_code}' --max-time 30 \
      "https://generativelanguage.googleapis.com/v1beta/models")
    if [ "$code" != "200" ]; then
      echo "    FAILED (http $code)"; head -c 300 "$TD/gk.json"; echo; exit 1
    fi
    n=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1])).get('models',[])))" "$TD/gk.json")
    echo "    ok - $n models visible"
    echo "2/2 can it actually GENERATE? (listing a model proves nothing - the free tier"
    echo "    lists every image model and then refuses to run one)"
    curl -s --max-time 120 -X POST -o "$TD/gk2.json" -K "$TD/curlrc" \
      -H "Content-Type: application/json" \
      -d '{"contents":[{"parts":[{"text":"a single grey circle on a white background"}]}]}' \
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent" >/dev/null
    python3 - "$TD/gk2.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if 'error' in d:
    e = d['error']; msg = e.get('message', '')
    free = any('FreeTier' in str(v.get('quotaId', ''))
               for det in e.get('details', []) for v in det.get('violations', []))
    if e.get('code') == 429 and free:
        print("    NOT BILLABLE - the key is on a free-tier project.")
        print("    Image generation has no free-tier allowance, so this will never work as is.")
        print("    Fix: open the Google Cloud project this key belongs to and ENABLE BILLING")
        print("    (console.cloud.google.com -> Billing -> link a billing account), then re-run.")
    else:
        print(f"    FAILED ({e.get('code')} {e.get('status')}): {msg[:160]}")
    sys.exit(1)
parts = d.get('candidates', [{}])[0].get('content', {}).get('parts', [])
img = [p for p in parts if 'inlineData' in p]
if img:
    import base64
    n = len(base64.b64decode(img[0]['inlineData']['data']))
    print(f"    ok - generated {n} bytes ({img[0]['inlineData']['mimeType']}). Billing is live.")
    print("    that call cost roughly $0.07.")
else:
    print("    responded, but returned no image. Parts:", [list(p) for p in parts])
    sys.exit(1)
PY
    ;;

  rm)
    secret-tool clear service "$SERVICE" key "$ATTR" && echo "removed" >&2
    ;;

  *) sed -n '2,8p' "$0"; exit 2 ;;
esac
