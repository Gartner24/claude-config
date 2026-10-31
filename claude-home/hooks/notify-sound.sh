#!/usr/bin/env bash
# Notification: the done sound. Spec 0082 AC-8: afplay on a Mac, paplay on Linux (the command settings.json
# used to run itself). A missing player or sound file plays nothing and exits 0: a hook fails open.
if [ "$(uname -s)" = Darwin ]; then
  player=afplay sound=/System/Library/Sounds/Glass.aiff
else
  player=paplay sound=/usr/share/sounds/ocean/stereo/outcome-success.oga
fi
if command -v "$player" >/dev/null 2>&1 && [ -e "$sound" ]; then
  "$player" "$sound" >/dev/null 2>&1
fi
exit 0
