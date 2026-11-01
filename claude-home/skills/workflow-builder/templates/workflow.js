// follows icm-architect 8bc2f5610d3843b3ffa31a142effe6b6337fef3c
// Spec 0076 AC-3. Fill every {{...}}. One phase per stage folder, in order: the meta titles, the phase() calls and each
// agent's phase, model and effort must match stages/NN_<stage>/ and its `Model:` line (check.py compares them).
// Copy the single agent block for each sequential stage; keep the fan out block only for the stage that fans out.
export const meta = {
  name: '{{name}}',
  description: '{{one line, shown in the permission dialog}}',
  phases: [
    { title: '01_{{stage}}', detail: '{{job}}' },
    { title: '02_{{stage}}', detail: '{{job}}' },
  ],
}

// The named args from the interview, filled by the starter skill before the run. limit is null unless --limit.
for (const key of ['repo', 'runId', '{{named arg}}']) {
  if (args == null || args[key] === undefined || args[key] === null || args[key] === '') {
    throw new Error(`missing arg: ${key}`)
  }
}

const NAME = '{{name}}'
const WF = `~/.claude/workflows/${NAME}`
const RUN = `${args.repo}/.workflow/runs/${NAME}/${args.runId}`

// Every agent returns this. A stage that needs more fields adds them; summary and outputs stay.
const STAGE = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    outputs: { type: 'array', items: { type: 'string' } },
    items: { type: 'array', items: { type: 'string' } },
    branch: { type: 'string' },
  },
  required: ['summary', 'outputs'],
}
// The stage that feeds a fan out must return its items: a missing list used to read as "0 of 0 item(s) done".
const LIST = { ...STAGE, required: [...STAGE.required, 'items'] }

const brief = (stage, before, extra) => [
  `Read ${WF}/stages/${stage}/CONTEXT.md and do that stage.`,
  `The repo is ${args.repo}. The run id is ${args.runId}.`,
  `Write your outputs to ${RUN}/${stage}/output/.`,
  before ? `The earlier stage returned: ${before}` : '',
  extra || '',
  'Then return the schema.',
].filter(Boolean).join('\n')

const stages = []

// A single agent stage. A stage that returns nothing stops the run: it is reported as failed, never as clean.
// This one feeds the fan out below, so it uses LIST; a sequential stage uses STAGE.
phase('01_{{stage}}')
const s1 = await agent(brief('01_{{stage}}', null), {
  label: '01_{{stage}}', model: '{{model}}', effort: '{{effort}}', schema: LIST,
})
stages.push(s1 ? { stage: '01_{{stage}}', ...s1 } : { stage: '01_{{stage}}', failed: true })
if (!s1) return { run: RUN, stages }

// A fan out stage: one agent per item of the earlier stage's `items`. isolation: 'worktree' and the branch lines only
// when its agents edit files; drop them for read only agents.
phase('02_{{stage}}')
if (!Array.isArray(s1.items)) {
  stages.push({ stage: '02_{{stage}}', summary: '01_{{stage}} returned no items list', failed: true, items: [], branches: [] })
  return { run: RUN, stages }
}
const all = s1.items
const items = args.limit ? all.slice(0, args.limit) : all
if (items.length < all.length) log(`--limit ${args.limit}: ${all.length - items.length} of ${all.length} item(s) not run`)
const branch = i => `wf/${NAME}-${args.runId}-02_{{stage}}-${i + 1}`
const fan = await pipeline(items, (item, _, i) => agent(brief('02_{{stage}}', s1.summary, [
  `Your item: ${item}`,
  `You run in your own git worktree: commit your code on a new branch ${branch(i)}. Never push or merge it.`,
  `Write your outputs to the run path above, which is in the main repo, never inside your worktree.`,
].join('\n')), {
  label: `02_{{stage}} ${i + 1}`, phase: '02_{{stage}}', model: '{{model}}', effort: '{{effort}}', schema: STAGE,
  isolation: 'worktree',
}))
const ok = fan.filter(Boolean)
if (ok.length < items.length) log(`02_{{stage}}: ${items.length - ok.length} of ${items.length} item(s) failed`)
stages.push({
  stage: '02_{{stage}}',
  summary: `${ok.length} of ${items.length} item(s) done`,
  failed: ok.length < items.length,
  items: ok,
  branches: ok.map(r => r.branch).filter(Boolean),
})

return { run: RUN, stages }
