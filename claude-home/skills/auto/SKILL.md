---
name: auto
description: Turn autonomous mode on or off for this chat. With it on, this session starts the wf runner itself for this chat's own repos whenever there is work and relays their questions and morning report (spec 0030, one chat per folder since spec 0046). Only the user starts it, and only the user releases a repo from a chat (`/auto release <repos>`).
disable-model-invocation: true
argument-hint: on [repos] | off [now] | release <repos>
---
Run nothing. When you typed `/auto on` (optionally followed by repo names), `/auto off`, `/auto off now` or `/auto release <repos>`, the prompt hook already switched autonomous mode for this chat as you (Claude can never run `wf auto on` or `wf auto release`: the command refuses them, and deny rules block them and `wf auto hook`).

Tell the user, in one or two sentences, the `autonomous:` line the hook printed in this turn's context, plus any `left out`, `taken from`, `released:`, `refused:` or `usage:` line. If there is no such line, say the hook did not switch it and ask the user to type the same `/auto` command again in this chat.
