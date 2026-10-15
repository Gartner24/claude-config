---
name: auto
description: Turn autonomous mode on or off for this chat. With it on, this session starts the wf runner itself for this chat's own repos whenever there is work and relays their questions and morning report (spec 0030, one chat per folder since spec 0046). Only the user starts it.
disable-model-invocation: true
argument-hint: on [repos] | off | off now
---
Run nothing. When you typed `/auto on` (optionally followed by repo names), `/auto off` or `/auto off now`, the prompt hook already switched autonomous mode for this chat as you (Claude can never run `wf auto on`; a deny rule blocks it, skills included).

Tell the user, in one or two sentences, the `autonomous:` line the hook printed in this turn's context, plus any `left out` or `taken from` line. If there is no such line, say the hook did not switch it and that typing `! wf auto on` (or `! wf auto off`) in this chat does the same thing.
