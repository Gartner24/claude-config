#!/bin/bash
# P6: which project folder gets the chat when claude starts in a symlinked folder?
T=$(mktemp -d)
mkdir $T/real
ln -s $T/real $T/link
cd $T/link
claude -p "Reply with only OK." --output-format json > /dev/null
P=$HOME/.claude/projects
R=$P/$(echo $T/real | sed 's#[/.]#-#g')
L=$P/$(echo $T/link | sed 's#[/.]#-#g')
echo "P6 real path folder: $(ls $R 2>&1)"
echo "P6 typed path folder: $(ls $L 2>&1)"
rm -rf $R $L $T
