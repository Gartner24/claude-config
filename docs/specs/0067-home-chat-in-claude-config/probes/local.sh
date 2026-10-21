#!/bin/bash
# P4: does Claude Code load CLAUDE.local.md from the start folder?
D=$(mktemp -d)
printf -- '- The local rule word is HERON77.\n' > $D/CLAUDE.local.md
cd $D
echo "P4: $(claude -p 'What is the local rule word in your project instructions? Reply with only the word, or NONE.' --output-format json | jq -r .result)"
rm -rf $HOME/.claude/projects/$(echo $D | sed 's#[/.]#-#g') $D
