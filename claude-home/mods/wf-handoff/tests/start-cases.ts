// Spec 0070 F1: one case list for the mod's chat start rule (tests/start.test.ts) and for
// workflow-start.sh --test, so the two copies of the rule cannot drift apart. The hook's test reads
// the JSON between the markers below with a JSON parser: keep it strict JSON (double quotes, no
// trailing commas, no comments inside). Org names are made up; the real list lives only in
// ~/.claude/private/work.md (public repo).
// Fields: origin "" = no remote; start = what the mod runs (null = nothing). The hook prints its
// Workflow line exactly when the folder is a git repo and the mod starts nothing.
// nowork: ~/.claude/private/work.md is missing (review fix 3: start nothing, the hook prints).
export type StartCase = { name: string; origin: string; repo: boolean; agents: boolean; scope: boolean; slot: boolean; start: 'audit' | 'scope' | null; nowork?: boolean }
export const FIXTURE: { work: string; cases: StartCase[] } = /* json:start */ {
  "work": "- **Bot-reviewed repos - origin under `github.com:team-org/` or `github.com:other-org/` - run NO local review.**",
  "cases": [
    { "name": "own repo, no AGENTS.md", "origin": "git@github.com:me/own.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": "audit" },
    { "name": "own repo with AGENTS.md", "origin": "https://github.com/me/own.git", "repo": true, "agents": true, "scope": true, "slot": false, "start": "scope" },
    { "name": "no remote at all", "origin": "", "repo": true, "agents": true, "scope": false, "slot": false, "start": "scope" },
    { "name": "not a git repo", "origin": "", "repo": false, "agents": false, "scope": false, "slot": false, "start": null },
    { "name": "a live handover slot", "origin": "git@github.com:me/own.git", "repo": true, "agents": true, "scope": true, "slot": true, "start": null },
    { "name": "bot org, scp form, no scope", "origin": "git@github.com:team-org/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": null },
    { "name": "bot org, https, other case, with a scope", "origin": "https://github.com/Team-Org/site.git", "repo": true, "agents": false, "scope": true, "slot": false, "start": "scope" },
    { "name": "bot org, ssh url, no scope", "origin": "ssh://git@github.com/team-org/site.git", "repo": true, "agents": true, "scope": false, "slot": false, "start": null },
    { "name": "bot org, ssh url with a port, no scope", "origin": "ssh://git@GitHub.com:22/other-org/x.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": null },
    { "name": "bot org, ssh url with a port and a scope", "origin": "ssh://git@GitHub.com:22/other-org/x.git", "repo": true, "agents": true, "scope": true, "slot": false, "start": "scope" },
    { "name": "bot org, scp form, with a scope", "origin": "git@github.com:team-org/site.git", "repo": true, "agents": true, "scope": true, "slot": false, "start": "scope" },
    { "name": "bot org in upper case, no scope", "origin": "git@github.com:TEAM-ORG/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": null },
    { "name": "lookalike org ending in a listed name", "origin": "git@github.com:myteam-org/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": "audit" },
    { "name": "lookalike host starting with github.com", "origin": "https://github.com.evil.example/team-org/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": "audit" },
    { "name": "listed text inside another host's path", "origin": "https://evil.example/github.com:team-org/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": "audit" },
    { "name": "listed org on another host", "origin": "git@gitlab.com:team-org/site.git", "repo": true, "agents": false, "scope": false, "slot": false, "start": "audit" },
    { "name": "no org list (work.md missing)", "origin": "git@github.com:me/own.git", "repo": true, "agents": true, "scope": true, "slot": false, "start": null, "nowork": true },
    { "name": "no org list and no remote", "origin": "", "repo": true, "agents": false, "scope": false, "slot": false, "start": null, "nowork": true },
    { "name": "an origin that does not parse", "origin": "/srv/git/site.git", "repo": true, "agents": true, "scope": true, "slot": false, "start": null }
  ]
} /* json:end */
