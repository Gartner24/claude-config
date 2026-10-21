#!/bin/bash
# P1-P3: does Claude Code follow a symlinked ~/.claude/projects/<folder> for memory, new chats and --resume?
set -u
T=$(mktemp -d)
H1=$T/homea
H2=$T/homeb
TGT=$T/target
mkdir -p $H1 $H2 $TGT/memory
printf -- '- [Probe word](probe.md) - the probe word is PELICAN42\n' > $TGT/memory/MEMORY.md
printf -- '---\nname: probe\ndescription: probe word\nmetadata:\n  type: reference\n---\nThe probe word is PELICAN42.\n' > $TGT/memory/probe.md
P=$HOME/.claude/projects
S1=$P/$(echo $H1 | sed 's#[/.]#-#g')
S2=$P/$(echo $H2 | sed 's#[/.]#-#g')
ln -s $TGT $S1
ln -s $TGT $S2
cd $H1
echo "P1: $(claude -p 'What is the probe word in your memory? Reply with only the word.' --output-format json > $T/p1.json; jq -r .result $T/p1.json)"
SID=$(jq -r .session_id $T/p1.json)
echo "P2: $(ls $TGT/$SID.jsonl)"
cd $H2
echo "P3: $(claude -p --resume $SID 'Repeat the probe word you gave before. Reply with only the word.' --output-format json | jq -r .result)"
rm -f $S1 $S2
rm -rf $T
