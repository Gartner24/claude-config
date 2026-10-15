# Autonomous mode per chat

Source: your messages of 2026-10-14 (about the "AUTO running 4 repos" status bar), confirmed in chat.

## Agreed so far, do not ask again

- Built tonight with the rest of the runner work (answered 2026-10-15, about 00:50: "Tonight too"), not later.
- Today one chat owns autonomous mode for every allowed repo. Wanted: several autonomous chats at once, each owning its own group of repos. Example: this chat (`~/.claude`) runs claude-config, maybe dotfiles, and general computer tasks; a chat opened in a work repo runs that repo plus its two related work repos.
- Each chat runs its own runner for only its repos. Its questions, progress and reports show in that chat, so the conversation's context stays with those repos. Turning one off does not touch the others.
- Which repos: everything accepted by default, or a named group per chat (for example `/auto on` with a list of repos).
- The group can be changed later, including moving a repo to another chat or session.
- Which repos (answered 2026-10-15): the chat's own repo plus any you name; and the chat recommends a set itself (the repos most likely to belong together, by its own criteria) and asks you to pick with a multiple choice panel.
- A repo another chat already runs (answered 2026-10-15): refuse to take it until its context can pass to the new chat, so no quality is lost. Both "take it" and "refuse until released" were good ideas to you; the deciding point is that the move carries the old chat's context along.
- Phone (answered 2026-10-15): the same Telegram chat for now. Owed later: a way to keep groups apart, since many things will land in one chat.

## Related bug (fix now, not part of this feature)

- The status bar says "running N repos" but counts runner locks, and parallel features each hold one: "4 repos" was 4 features of claude-config. It should name features and repos correctly (`runner/auto.py` status_line and the bar segment).
