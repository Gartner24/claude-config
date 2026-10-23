#!/usr/bin/env bash
# Spec 0051 AC-10: a repo's merge settings and its one branch ruleset, so code reaches the default branch only
# through a squash merged PR and a merged branch is deleted. Run by you or a session, never by wf (wf only reads
# them at each run start). --check only reads, prints each difference and exits 1 on any.
# GH names the gh binary; the self checks point it at a fake, never at GitHub.
set -euo pipefail

GH="${GH:-gh}"
NAME="main only through a PR"
usage() { echo "usage: tools/bin/repo-settings.sh [--check] <owner/repo>" >&2; exit 2; }

check=0
repo=""
for a in "$@"; do
  case "$a" in
    --check) check=1 ;;
    -*) usage ;;
    *) [[ -z "$repo" ]] || usage; repo="$a" ;;
  esac
done
[[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || usage

# The settings as GitHub's API names them, and the value each must have.
SETTINGS=(allow_squash_merge=true allow_merge_commit=false allow_rebase_merge=false delete_branch_on_merge=true
          squash_merge_commit_title=PR_TITLE squash_merge_commit_message=PR_BODY)

ruleset_id() {
  "$GH" api "repos/$repo/rulesets" --jq ".[] | select(.name == \"$NAME\") | .id" | head -n 1
}

differences() {
  local off=0 have key want id
  for kv in "${SETTINGS[@]}"; do
    key="${kv%%=*}" want="${kv#*=}"
    have="$("$GH" api "repos/$repo" --jq ".$key")"
    if [[ "$have" != "$want" ]]; then
      echo "$key is $have, wants $want"
      off=1
    fi
  done
  id="$(ruleset_id)"
  if [[ -z "$id" ]]; then
    echo "no ruleset named '$NAME'"
    return 1
  fi
  # One line naming the ruleset's shape; anything else is a difference.
  have="$("$GH" api "repos/$repo/rulesets/$id" --jq '[.enforcement, .target, (.conditions.ref_name.include | join(",")),
    ([.rules[].type] | sort | join(",")),
    ([.rules[] | select(.type == "pull_request") | .parameters.required_approving_review_count] | join(",")),
    (.bypass_actors | length)] | map(tostring) | join(" ")')"
  want="active branch ~DEFAULT_BRANCH deletion,non_fast_forward,pull_request 0 0"
  if [[ "$have" != "$want" ]]; then
    echo "ruleset '$NAME' is: $have; wants: $want"
    off=1
  fi
  return "$off"
}

if [[ "$check" == 1 ]]; then
  differences && exit 0
  exit 1
fi

args=()
for kv in "${SETTINGS[@]}"; do
  case "${kv#*=}" in true|false) args+=(-F "$kv") ;; *) args+=(-f "$kv") ;; esac
done
"$GH" api -X PATCH "repos/$repo" "${args[@]}" >/dev/null

body="$(cat <<EOF
{"name": "$NAME", "target": "branch", "enforcement": "active", "bypass_actors": [],
 "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
 "rules": [{"type": "pull_request", "parameters": {"required_approving_review_count": 0,
            "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false,
            "require_last_push_approval": false, "required_review_thread_resolution": false}},
           {"type": "non_fast_forward"}, {"type": "deletion"}]}
EOF
)"
id="$(ruleset_id)"
if [[ -n "$id" ]]; then
  printf '%s' "$body" | "$GH" api -X PUT "repos/$repo/rulesets/$id" --input - >/dev/null
else
  printf '%s' "$body" | "$GH" api -X POST "repos/$repo/rulesets" --input - >/dev/null
fi
# GitHub's rulesets list can lag a moment behind the POST, so a fresh ruleset is not listed yet: read it back with retries.
for try in 1 2 3 4 5 6; do
  differences && { echo "repo-settings: $repo set"; exit 0; }
  [[ "$try" == 6 ]] || sleep "${RS_SLEEP:-2}"
done
exit 1
