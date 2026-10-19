import type { EngineInterface, PluginOptions, Register } from 'claude-code'
import { extractFacts, factsBlock, fillTemplate, insertAfterHeading, lastRequestStatus, markUnverified, type Numbers } from '../facts.ts'

type Phase = 'idle' | 'gated' | 'rolling' | 'clearing' | 'seeding' | 'paused' | 'failed'
type Chain = {
  root: string; session: string; previous: string | null; startTokens: number | null; unattended: number
  triggeredAt: string | null; phase: Phase; lastRequest: string | null; link?: string
}

const GATE_TEXT = 'context is at the handoff line; finish this turn in words, the handoff starts at the end of it'
const HOLD_TEXT = 'held for the handoff; it is sent for you, clear the box'
const PAUSE_TEXT = 'auto handoff paused: type anything to resume'
const EXEMPT = ['rollover', 'save-and-clear', 'handoff']
const CLEAR_TIMEOUT_MS = 15000

let opts: PluginOptions = {}
let threshold = 200000
let headroom = 40000
let maxInRow = 2
let ignoreFiles = ''

let active = false
let home = ''
let envTokens: number | null = null
let dir = ''
let chain: Chain | null = null
let pending = 0 // tool output characters the last usage figure does not hold yet
let exemptTurn = false
let armedTurn: string | null = null
let currentTurn: string | null = null
let rollResolved = false
let awaitStart = false
let counted = false
let held: string[] = []
let clearGen = 0
let logQueue = Promise.resolve()

async function slotCmd($: EngineInterface) {
  const cwd = await $.session.cwd()
  return $.process.run(
    [`${home}/.claude/skills/jjstack/bin/jjstack-rollover-slot`, '--cwd', cwd, 'status', '--max-age-days', '1'],
    { timeoutMs: 2000 },
  ).catch(() => ({ exitCode: 1, stdout: '' }))
}

function log($: EngineInterface, text: string) {
  logQueue = logQueue.then(async () => {
    const path = `${dir}/auto-handoff.log`
    const old = await $.fs.read(path).catch(() => '')
    const now = new Date(await $.clock.now()).toISOString()
    await $.fs.write(path, `${old}${now} ${chain?.session ?? '-'} ${text}\n`)
  }).catch(() => {})
  return logQueue
}

async function save($: EngineInterface) {
  if (chain) await $.fs.write(`${dir}/${chain.root}.json`, JSON.stringify(chain, null, 2) + '\n').catch(() => {})
}

async function setPhase($: EngineInterface, phase: Phase) {
  chain!.phase = phase
  await save($)
}

function lineNow() {
  const base = envTokens ?? threshold
  const source = envTokens != null ? 'AUTO_HANDOFF_TOKENS' : 'threshold setting'
  const start = chain?.startTokens
  if (start != null && start + headroom > base) return { line: start + headroom, source: 'start plus headroom' }
  return { line: base, source }
}

async function size($: EngineInterface) {
  return ((await $.session.usage()).context.tokens ?? 0) + Math.ceil(pending / 4)
}

// True when the line is crossed and the mod may act; past the guard it pauses instead.
async function crossed($: EngineInterface) {
  if (!chain || exemptTurn || (chain.phase !== 'idle' && chain.phase !== 'gated')) return false
  if (chain.phase === 'gated') return true
  if ((await size($)) <= lineNow().line) return false
  if (chain.unattended >= maxInRow) {
    await setPhase($, 'paused')
    $.ui.toast(PAUSE_TEXT); $.ui.status(PAUSE_TEXT)
    await log($, `paused after ${chain.unattended} handoffs in a row`)
    return false
  }
  return true
}

async function arm($: EngineInterface, turnId: string | null, why: string) {
  if (chain!.phase !== 'gated') await log($, `trigger: ${why}, size ${await size($)}, line ${lineNow().line}`)
  armedTurn = turnId
  await setPhase($, 'gated')
}

async function fail($: EngineInterface, text: string) {
  if (!counted) { chain!.unattended++; counted = true }
  await setPhase($, 'failed')
  $.ui.toast(`auto handoff failed: ${text}`, { timeoutMs: 10000 })
  $.ui.status(`auto handoff failed: ${text}`)
  await log($, `failed: ${text}`)
}

async function template($: EngineInterface, name: 'sections' | 'instructions') {
  const set = String(opts[`${name}Template`] ?? '').trim()
  const path = set ? set.replace(/^~(?=\/)/, home) : `${home}/.claude/auto-handoff/${name}.md`
  return $.fs.read(path).catch(() => $.fs.read(`${$.plugin.root}/templates/${name}.md`))
}

async function startHandoff($: EngineInterface) {
  const c = chain!
  c.triggeredAt = new Date(await $.clock.now()).toISOString()
  rollResolved = false
  counted = false
  await setPhase($, 'rolling')
  const args = fillTemplate(await template($, 'sections'), {
    priority: false, lastRequest: c.lastRequest ?? '(none typed in this chat)',
  })
  await log($, 'rollover started')
  // Probe P1: slash commands go through $.command.run (prompt.submit refuses them); P6: it
  // resolves when the rollover turn starts, so its end is the next main turn.complete.
  $.command.run({ command: 'rollover', args }).then(
    () => { rollResolved = true },
    err => fail($, `the rollover did not start (${err})`),
  )
}

async function finishRollover($: EngineInterface) {
  const c = chain!
  const r = await slotCmd($)
  const path = r.exitCode === 0 ? r.stdout.trim() : ''
  const stat = path ? await $.fs.stat(path).catch(() => null) : null
  if (!stat || stat.mtimeMs <= Date.parse(c.triggeredAt!)) {
    await log($, 'slot missing: the rollover wrote no new handover')
    return fail($, 'the rollover wrote no new handover; nothing was cleared')
  }
  await log($, `slot found: ${path}`)
  const n: Numbers = {
    tokens: await size($), line: lineNow().line, lineSource: lineNow().source,
    start: c.startTokens, unattended: c.unattended,
  }
  const facts = extractFacts(await $.session.messages(), ignoreFiles)
  const marked = markUnverified(await $.fs.read(path), n)
  for (const f of marked.marked) await log($, `unverified figure: ${f}`)
  const slot = insertAfterHeading(marked.text, factsBlock(facts, n, c.link))
  await $.fs.write(path, slot)
  await setPhase($, 'clearing')
  const gen = ++clearGen
  $.clock.after(1000, async () => {
    // Probe P3: no session.start after /clear; the seed runs once the awaited clear resolved,
    // when handover-start.sh has already loaded the slot text.
    const timedOut = $.clock.sleep(CLEAR_TIMEOUT_MS).then(() => 'timeout' as const)
    const cleared = $.command.run({ command: 'clear', args: '' }).then(() => 'ok' as const, () => 'error' as const)
    const how = await Promise.race([cleared, timedOut])
    if (gen !== clearGen || c.phase !== 'clearing') return
    if (how !== 'ok') {
      clearGen++ // a late resolve is ignored: no seed
      return fail($, `the clear ${how === 'timeout' ? 'did not finish in 15 s' : 'failed'}; the chat may still have cleared`)
    }
    await seed($, slot)
  })
}

async function seed($: EngineInterface, slot: string) {
  const c = chain!
  c.previous = c.session
  c.session = await $.session.id()
  c.startTokens = null
  c.unattended++
  counted = true
  awaitStart = true
  pending = 0
  await setPhase($, 'seeding')
  const priority = lastRequestStatus(slot) === 'not answered'
  const args = fillTemplate(await template($, 'instructions'), { priority, lastRequest: c.lastRequest ?? '' })
  await log($, `cleared; seed run (priority ${priority ? 'on' : 'off'})`)
  $.command.run({ command: 'resume-from-clear', args }).catch(err =>
    fail($, `the fresh chat did not start (${err}); the handover waits, type /resume-from-clear`))
  await setPhase($, 'idle')
  const resend = held
  held = []
  for (const text of resend) {
    const m = text.match(/^\/(\S+)\s*([\s\S]*)$/)
    if (m) void $.command.run({ command: m[1]!, args: m[2] ?? '' }).catch(() => {})
    else void $.prompt.submit({ text }).catch(() => {})
    await log($, 'held prompt sent again')
  }
}

// Spec 0057 AC-10: /handoff replaces typing /clear after a /rollover. The clear empties the
// context and handover-start.sh (SessionStart, clear) then loads the handover; that hook is
// the fallback when this mod is gone or breaks on an update.
// Spec 0063: the same mod also hands off on its own at the token line (AC-1 to AC-12).
export const register: Register = (on, options) => {
  opts = options
  threshold = Number(options.threshold ?? 200000)
  headroom = Number(options.minHeadroom ?? 40000)
  maxInRow = Number(options.maxConsecutiveHandoffs ?? 2)
  ignoreFiles = String(options.ignoreFiles ?? '')

  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({ name: 'handoff', description: 'After /rollover: clear and load the waiting handover' })
    home = (await $.env.get('HOME')) ?? ''
    dir = `${home}/.claude/state/auto-handoff`
    active = e.isInteractive && !(await $.env.get('WF_RUN')) && !(await $.env.get('TM_WORKER_NAME'))
      && (await $.env.get('AUTO_HANDOFF_DISABLE')) !== '1'
    if (!active) return started
    const t = Number(await $.env.get('AUTO_HANDOFF_TOKENS'))
    envTokens = t > 0 ? t : null
    for (const name of ['sections', 'instructions']) {
      const own = `${home}/.claude/auto-handoff/${name}.md`
      if ((await $.fs.read(own).catch(() => null)) === null)
        await $.fs.write(own, await $.fs.read(`${$.plugin.root}/templates/${name}.md`)).catch(() => {})
    }
    const id = await $.session.id()
    // A reload of the module (settings change) keeps the chain from its state file.
    for (const f of await $.fs.list(dir).catch(() => [])) {
      if (!f.name.endsWith('.json')) continue
      const c = await $.fs.read(`${dir}/${f.name}`).then(t => JSON.parse(t) as Chain).catch(() => null)
      if (c?.session === id) chain = c
    }
    chain ??= { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }
    return started
  })

  on('session.end', async ($, e, next) => {
    const r = await next(e)
    // An owner's own /clear starts a new chain and gets no seed.
    if (active && e.reason === 'clear' && chain && chain.phase !== 'clearing') {
      chain = null
      const id = await $.session.id().catch(() => '')
      if (id) chain = { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }
      pending = 0; awaitStart = false; exemptTurn = false
    }
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    if (!active || !chain) return next(e)
    const typed = e.origin.kind === 'composer' || e.origin.kind === 'bridge'
    const owner = typed && !e.command && !e.text.startsWith('/')
    if (typed && ['gated', 'rolling', 'clearing', 'seeding'].includes(chain.phase)) {
      held.push(e.text)
      if (owner) { chain.unattended = 0; chain.lastRequest = e.text; await save($) }
      await log($, `prompt held during ${chain.phase}`)
      // AC-2: an interrupted gated turn that never reached turn.complete hands off here.
      if (chain.phase === 'gated' && !e.turnId) void startHandoff($)
      return { drop: HOLD_TEXT }
    }
    if (owner) {
      chain.unattended = 0
      chain.lastRequest = e.text
      if (chain.phase === 'paused' || chain.phase === 'failed') { chain.phase = 'idle'; $.ui.status(undefined) }
      await save($)
    }
    if (EXEMPT.some(c => e.text === `/${c}` || e.text.startsWith(`/${c} `)) || EXEMPT.includes(e.command?.name ?? '')) exemptTurn = true
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    if (!active || e.agentId) return next(e)
    if (await crossed($)) {
      await arm($, currentTurn, `tool call ${e.tool} past the line`)
      await log($, `refused ${e.tool}`)
      return { deny: GATE_TEXT }
    }
    const r = await next(e)
    pending += r.text?.length ?? 0
    return r
  })

  on('turn.step', async function* ($, e, next) {
    if (!active || e.agentId || !chain) return yield* next(e)
    currentTurn = e.turnId
    // AC-2 fallback: a gated turn ended without turn.complete (Esc); the next step hands off.
    if (chain.phase === 'gated' && armedTurn !== e.turnId) {
      void startHandoff($)
      return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
    }
    if (chain.phase === 'idle' && (await crossed($))) {
      await arm($, e.turnId, 'model request past the line')
      // Probe P7: answering without next(e) sends no request and ends the turn.
      return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
    }
    const r = yield* next(e)
    pending = 0
    if (awaitStart) {
      // Probe P4: the size of a just cleared chat is known only after its first response.
      const tokens = (await $.session.usage()).context.tokens
      if (tokens != null) { chain.startTokens = tokens; awaitStart = false; await save($); await log($, `fresh chat starts at ${tokens}`) }
    }
    return r
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (!active || e.agentId || !chain) return r
    if (chain.phase === 'rolling') {
      if (rollResolved) { rollResolved = false; exemptTurn = false; await finishRollover($) }
      return r
    }
    const wasExempt = exemptTurn
    exemptTurn = false
    if (!wasExempt && (chain.phase === 'gated' || (await crossed($)))) {
      if (chain.phase !== 'gated') await arm($, e.turnId, 'turn ended past the line')
      await startHandoff($)
    }
    return r
  })

  on('command.run', { command: 'handoff' }, async $ => {
    home ||= (await $.env.get('HOME')) ?? ''
    const r = await slotCmd($)
    if (r.exitCode !== 0 || !r.stdout.trim()) return { text: 'no handover, run /rollover first' }
    // Probe P2: awaiting $.command.run inside a command.run hook is refused (it waits on the turn
    // this hook holds), so the clear runs from a timer after the hook has returned.
    $.clock.after(1500, () => {
      void $.command.run({ command: 'clear', args: '' })
    })
    return { text: `Handover found at ${r.stdout.trim()}; clearing in 1.5 s, then it loads.` }
  })
}
