#!/usr/bin/env bash
# Spec 0009 AC-11 P2: the app jail of AC-3 step 3, built by hand. A jailed server must answer from the host,
# and a jailed shell must not read keys, write home, write the repo's .claude or git hooks, or reach an agent socket.
set -u
R=$(mktemp -d)
trap 'kill $APP 2>/dev/null; rm -rf "$R"' EXIT
H=$HOME
PORT=${PORT:-8791}
git -C "$R" init -q
mkdir -p "$R/.claude"
printf '{}\n' > "$R/.claude/settings.json"
COMMON=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)

jail() {
  local a=(bwrap --die-with-parent --unshare-pid --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs /run)
  for p in "$R" "$H/.npm" "$H/.cache" "$H/.local/share/pnpm"; do [ -e "$p" ] && a+=(--bind "$p" "$p"); done
  for p in "$R/.claude" "$COMMON/config" "$COMMON/hooks"; do [ -e "$p" ] && a+=(--ro-bind "$p" "$p"); done
  for p in "$H/.ssh" "$H/.config/gh" "$H/.git-credentials" "$H/.netrc" "$H/.aws" "$H/.config/gcloud" "$H/.azure" \
           "$H/.gnupg" "$H/.claude/.credentials.json" "$H/.config/BraveSoftware"; do
    if [ -d "$p" ]; then a+=(--tmpfs "$p"); elif [ -e "$p" ]; then a+=(--ro-bind /dev/null "$p"); fi
  done
  "${a[@]}" --chdir "$R" /bin/sh -c "$1"
}

jail "exec python3 -m http.server $PORT --bind 127.0.0.1" >"$R/app.log" 2>&1 &
APP=$!
for _ in $(seq 40); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.25; done
echo "app from host: $(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/")"

SSHF=$(ls "$H/.ssh" | head -1)
jail "
cat \$HOME/.ssh/$SSHF >/dev/null 2>&1 && echo 'ssh read: OPEN' || echo 'ssh read: refused'
touch \$HOME/probe-wf 2>/dev/null && echo 'home write: OPEN' || echo 'home write: refused'
touch $R/probe 2>/dev/null && echo 'repo write: ok' || echo 'repo write: FAILED'
touch $COMMON/hooks/probe 2>/dev/null && echo 'git hooks write: OPEN' || echo 'git hooks write: refused'
echo x > $R/.claude/settings.json 2>/dev/null && echo '.claude write: OPEN' || echo '.claude write: refused'
for s in ${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/gnupg/S.gpg-agent ${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/gnupg/S.gpg-agent.ssh ${SSH_AUTH_SOCK:-/nonexistent}; do
  python3 -c 'import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1])' \$s 2>/dev/null && echo \"socket \$s: OPEN\" || echo \"socket \$s: refused\"
done
"
echo "after: ~/probe-wf $(test -e "$H/probe-wf" && echo exists || echo absent); $R/probe $(test -e "$R/probe" && echo exists || echo absent)"
rm -f "$H/probe-wf"
