This is an automatic handoff: the chat reached its handoff line, so write the full handover now and do not ask the owner anything. Do not tell the owner to type /clear; the wf-handoff mod clears and starts the fresh chat itself.
{{#transcript}}
This chat's transcript is {{transcript}}: name it as the previous transcript, do not search for the newest log.
{{/transcript}}

The fresh chat starts with nothing but this handover, and it cannot afford to reread this whole chat. Anything you leave out is lost. Write it rich, not short: the contract's "three to six sentences" and "anything else is padding" do not apply to this handover. Keep its fields, and keep the order below, most important first.

Add these sections to the handover, right after its next actions:

## Last request from the owner
> {{lastRequest}}
Status: answered or not answered (pick one: "answered" only when your replies fully did what it asks)

## What the owner said
Every message the owner typed in this chat, oldest first, as a quote. Copy each one word for word; shorten only a message over 400 characters, keeping its asks and corrections. Skip slash commands and pasted logs.

## Agreed so far, do not ask again
Every decision, answer and preference agreed in this chat, one line each with its reason. Say which ones are written down in a file (name it) and which live only here.

## Tried and failed, and gotchas
Every approach that did not work and why, every trap found (a wrong path, a flag that does nothing, a hook that blocks a command shape), and the working way round each one. The fresh chat must not repeat them.

## Key files and places
Each file, branch, PR, worktree or command that matters to the next steps, with one line on what is in it and its state now.

## Open questions and loose ends
Anything noticed but not done, promised to the owner, or waiting on someone, with who it waits on.

Never stop a background agent or task that is still running: name each one with its id under open questions, so the fresh chat picks up its result.

Leave out token counts and context sizes; the mod adds the real numbers itself.

Once the slot is written, end the turn with one short line: the chat is cleared a second later, and the fresh chat reads the handover, not a summary.
