---
name: auto
description: Turn autonomous mode on or off. With it on, this session starts the wf runner itself whenever there is work and relays its questions and morning report (spec 0030). Only the user starts it.
disable-model-invocation: true
argument-hint: on | off | off now
---
Run nothing. When you typed `/auto on`, `/auto off` or `/auto off now`, the prompt hook already switched autonomous mode as you (Claude can never run `wf auto on`; a deny rule blocks it, skills included).

Tell the user, in one sentence, the `autonomous:` line the hook printed in this turn's context. If there is no such line, say the hook did not switch it and that typing `! wf auto on` (or `! wf auto off`) in this chat does the same thing.
