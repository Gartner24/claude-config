// Spec 0074 AC-5 to AC-8: one worktree agent per picked row, all at once, each ending at a draft PR. The skill
// (SKILL.md beside this file) does the listing, asking, start gates and the review and merge; this only fans out.
export const meta = {
  name: 'build-features',
  description: 'Build each picked scope row in its own worktree through develop, the tier chain and a draft PR. Never merges.',
  phases: [
    { title: 'build', detail: 'One worktree agent per row: develop, verify, test, draft PR' },
  ],
}

if (args == null || typeof args.runId !== 'string' || !/^[A-Za-z0-9-]+$/.test(args.runId)) throw new Error('bad arg: runId')
if (!Array.isArray(args.rows) || args.rows.length === 0) throw new Error('bad arg: rows')
const SAFE = /^[A-Za-z0-9._\/-]+$/
for (const r of args.rows) {
  const bad = k => { throw new Error(`bad arg: rows[].${k} (${JSON.stringify(r && r[k])})`) }
  if (!Number.isInteger(r.row) || r.row < 1) bad('row')
  if (typeof r.feature !== 'string' || !r.feature.trim()) bad('feature')
  if (!/^\d{4}$/.test(String(r.spec))) bad('spec')
  if (!['haiku', 'sonnet', 'opus'].includes(r.model)) bad('model')
  if (!['low', 'medium', 'high'].includes(r.effort)) bad('effort')
  if (!Number.isInteger(r.cores) || r.cores < 1) bad('cores')
  if (!['Prototype', 'Alpha', 'Beta', 'GA'].includes(r.tier)) bad('tier')
  if (typeof r.base !== 'string' || !SAFE.test(r.base) || r.base.startsWith('-')) bad('base')
}

// rules-on-demand/branch-pr.md rule 1: feat/<spec>-<slug>, fix/ when the heading starts with "Fix"; the row number is not part of it
const branchOf = r => {
  const title = r.feature.replace(/^\d+\.\s*/, '')
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `${/^fix\b/i.test(title) ? 'fix' : 'feat'}/${r.spec}-${slug}`
}

const CHAIN = {
  Prototype: [],
  Alpha: [['verify', '/check verify']],
  Beta: [['verify', '/check verify'], ['test', '/test']],
  GA: [['verify', '/check verify'], ['test', '/test']],
}

const RESULT = {
  type: 'object',
  properties: {
    row: { type: 'integer' },
    status: { type: 'string', enum: ['pr', 'failed', 'skipped'] },
    branch: { type: 'string' },
    pr_url: { type: 'string' },
    step: { type: 'string' },
    reason: { type: 'string' },
  },
  required: ['row', 'status', 'branch', 'pr_url', 'step', 'reason'],
}

const brief = r => {
  const dir = `~/.claude/state/build-features/${args.runId}`
  const mark = s => `mkdir -p ${dir} && printf ${s} > ${dir}/row-${r.row}.step`
  const name = r.feature.replace(/^\d+\.\s*/, '')
  const branch = branchOf(r)
  const steps = [
    `0. git fetch origin, then git switch -c '${branch}' 'origin/${r.base}'.`,
    `1. Run: ${mark('develop')}. Then run the skill /develop ${name}.`,
    ...CHAIN[r.tier].map(([s, cmd], i) => `${i + 2}. Run: ${mark(s)}. Then run the skill ${cmd} ${name}.`),
    `${CHAIN[r.tier].length + 2}. Run: ${mark('pr')}.` +  ' Write the PR body with the skill /document pr.' +
      ` Squash your commits into one Conventional Commit on '${branch}' (rules-on-demand/branch-pr.md), push it with git push -u origin '${branch}' (if it hangs, retry with git -c protocol.version=0), then gh pr create --draft --base '${r.base}' --head '${branch}'.`,
  ]
  return [
    `You build scope row ${r.row} ("${name}", spec ${r.spec}) in your own git worktree, unattended. Run id: ${args.runId}.`,
    `Tier ${r.tier}. Run the test suite with at most ${r.cores} cores (WF_CORES=${r.cores}).`,
    'Before each step write its step file with the command given; a failed write never stops the build.',
    ...steps,
    'A step that fails: run the skill /debug, under rules/stop-and-reset.md (after 2 failed fixes on the same cause, stop).',
    'A stopped build pushes nothing and returns status failed with the step and the reason; keep the branch.',
    '/develop finding an owed decision (it would route to /architect or ask the owner): push nothing and return status skipped with reason "needs a decision: <the question>".',
    'Nobody can answer you: never ask, never merge, never mark the PR ready.',
    `Return the schema: row ${r.row}, status pr|failed|skipped, branch '${branch}', pr_url ("" when none), step (the last step file word), reason ("" when none).`,
  ].join('\n')
}

phase('build')
const results = await parallel(args.rows.map(r => () => agent(brief(r), {
  label: `row ${r.row} · ${r.feature.replace(/^\d+\.\s*/, '').slice(0, 30)}`,
  phase: 'build', model: r.model, effort: r.effort, isolation: 'worktree', schema: RESULT,
})))

// the row and branch come from the args, never from the agent; an agent that returned nothing is failed
return args.rows.map((r, i) => {
  const got = results[i]
  if (!got) return { row: r.row, status: 'failed', branch: branchOf(r), pr_url: '', step: 'unknown', reason: 'the agent returned nothing' }
  if (got.branch !== branchOf(r)) log(`row ${r.row}: agent reported branch ${JSON.stringify(got.branch)}, kept ${branchOf(r)}`)
  return { ...got, row: r.row, branch: branchOf(r) }
})
