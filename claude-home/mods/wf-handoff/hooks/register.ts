import type { EngineInterface, PluginOptions, Register } from 'claude-code'
import { extractFacts, factsBlock, fillTemplate, insertAfterHeading, lastRequestStatus, markUnverified, type Numbers } from '../facts.ts'
import { addNext, renderPage } from '../pages.ts'

type Phase = 'idle' | 'gated' | 'rolling' | 'clearing' | 'seeding' | 'paused' | 'failed'
type Chain = {
  root: string; session: string; previous: string | null; startTokens: number | null; unattended: number
  triggeredAt: string | null; phase: Phase; lastRequest: string | null; link?: string; pageKey?: string
  answered?: boolean // false from an owner prompt until a turn ends without the gate
}

const GATE_TEXT = 'context is at the handoff line; finish this turn in words, the handoff starts at the end of it'
const HOLD_TEXT = 'held for the handoff; it is sent for you, clear the box'
const PAUSE_TEXT = 'auto handoff paused: type anything to resume'
const EXEMPT = ['rollover', 'save-and-clear', 'handoff']
const CLEAR_TIMEOUT_MS = 15000
// shortcut: the log is cut to its newer half past this size; one log is shared by every chat
const LOG_MAX = 256000
// Spec 0064 AC-1: the steps the wf-dash band draws from panel.json.
const STEPS = ['writing the handover', 'clearing', 'starting the fresh chat']
const STICKY_TOAST_MS = 30000

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
let exemptNext = false // an exempt command typed mid turn: it runs as the next turn
let requestAtTrigger: string | null = null
let answeredAtTrigger = true
let armedTurn: string | null = null
let currentTurn: string | null = null
let rollResolved = false
let awaitStart = false
let counted = false
let held: string[] = []
let clearGen = 0
let lateClear = false // a timed out handoff clear may still end the chat
let pointed = ''
let logQueue = Promise.resolve()
let panelStep = -1 // the running step of the panel, STEPS.length once all are done
let panelResult: string | null = null
let handoffTokens = 0
let viewerBase = '' // http://<bind>:<port>, or '' for file links
let nextFor: { page: string; link: string } | null = null

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
    // this used to grow forever, and every line rereads and rewrites the whole file
    let old = await $.fs.read(path).catch(() => '')
    if (old.length > LOG_MAX) old = old.slice(old.indexOf('\n', old.length - LOG_MAX / 2) + 1)
    const now = new Date(await $.clock.now()).toISOString()
    await $.fs.write(path, `${old}${now} ${chain?.session ?? '-'} ${text}\n`)
  }).catch(() => {})
  return logQueue
}

async function save($: EngineInterface) {
  if (!chain) return
  await $.fs.write(`${dir}/${chain.root}.json`, JSON.stringify(chain, null, 2) + '\n').catch(() => {})
  // session.start finds a handed off chat's chain through this pointer instead of parsing every chain file
  if (chain.session !== chain.root && pointed !== chain.session) {
    pointed = chain.session
    await $.fs.write(`${dir}/${chain.session}.root`, chain.root).catch(() => {})
  }
}

async function setPhase($: EngineInterface, phase: Phase) {
  chain!.phase = phase
  await save($)
  await writePanel($)
}

// AC-1: one file for the band; `previous` lets the fresh chat match a panel its old id wrote.
async function writePanel($: EngineInterface) {
  const c = chain!
  const failed = c.phase === 'failed'
  const steps = STEPS.map((label, i) => ({
    label, state: i < panelStep ? 'done' : i === panelStep ? (failed ? 'failed' : 'running') : 'pending',
  }))
  const p = {
    session: c.session, previous: c.previous, phase: c.phase, steps, result: panelResult,
    sticky: failed || c.phase === 'paused', link: c.link ?? null, at: await $.clock.now(),
  }
  await $.fs.write(`${dir}/panel.json`, JSON.stringify(p) + '\n').catch(() => {})
}

// AC-3: a toast only where no band draws the panel: wf-dash not loaded, or a surface it skips.
async function notify($: EngineInterface, text: string, sticky = false) {
  const surfaces = await $.session.surfaces().catch(() => [] as readonly string[])
  const dash = surfaces.some(s => s !== 'terminal') ? null
    : await $.state.get({ plugin: 'wf-dash', key: 'facts' } as any).catch(() => null)
  if (dash && dash.version > 0) return
  $.ui.toast(text, sticky ? { timeoutMs: STICKY_TOAST_MS } : undefined)
}

const k = (n: number) => `${Math.round(n / 1000)}k`

function randomKey() {
  return [...crypto.getRandomValues(new Uint8Array(8))].map(b => b.toString(16).padStart(2, '0')).join('')
}

// AC-5: Tailscale's IPv4 address when `tailscale ip -4` answers, else loopback; never any other.
async function startServer($: EngineInterface) {
  const v = String(opts.viewer ?? 'tailscale:3846').trim()
  if (!v) return
  const m = v.match(/^(?:(.+):)?(\d{1,5})$/)
  if (!m || Number(m[2]) > 65535) { await log($, `viewer setting "${v}" is not [host:]port; no server`); return }
  const port = Number(m[2])
  const ts = await $.process.run(['tailscale', 'ip', '-4'], { timeoutMs: 2000 }).catch(() => null)
  const tsIp = ts?.exitCode === 0 ? ts.stdout.trim().split('\n')[0]!.trim() : ''
  const loopback = m[1] === '127.0.0.1' || m[1] === 'localhost'
  const bind = !loopback && /^100\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(tsIp) ? tsIp : '127.0.0.1'
  viewerBase = `http://${bind}:${port}`
  for (const host of new Set([bind, '127.0.0.1', tsIp].filter(Boolean))) {
    // server.py --probe checks the server signs this fresh nonce with the private token (this runtime
    // has no HMAC); an answer recorded earlier signs an old nonce and is not ours
    const r = await $.process.run(['python3', `${$.plugin.root}/server.py`, '--probe', host, String(port), `${dir}/server.token`, randomKey()], { timeoutMs: 5000 }).catch(() => null)
    const info = (() => { try { return JSON.parse(r?.stdout ?? '') } catch { return null } })()
    if (!info || info.state === 'none') continue
    if (info.state !== 'ours') {
      // never send the phone to a listener we cannot prove is ours: file links instead
      viewerBase = ''
      await log($, `port ${port} on ${host} is taken by something else; no server, file links`)
      return
    }
    if (info.bind === bind) return // another session serves already
    // Tailscale came up (or went): stop the old server, but only a process that is ours.
    const cmd = await $.fs.read(`/proc/${Number(info.pid)}/cmdline`).catch(() => '')
    if (!/wf-handoff\/server\.py/.test(cmd)) { await log($, `server on ${host}:${port} is not this mod's; left alone`); return }
    await $.process.run(['kill', String(Number(info.pid))]).catch(() => null)
    await log($, `stopped the server on ${info.bind}, now ${bind}`)
  }
  void (async () => {
    try {
      const out = $.process.spawn({ argv: ['python3', `${$.plugin.root}/server.py`, '--bind', bind, '--port', String(port), '--dir', `${dir}/pages`, '--token-file', `${dir}/server.token`] })
      for await (const { text } of out) {
        // the port went to something else between the probe and the bind: no links to it
        if (/not free|refused bind/.test(text)) viewerBase = ''
        await log($, `server: ${text.trim()}`)
      }
    } catch (err) {
      await log($, `server did not start (${err})`)
    }
  })()
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
    panelStep = -1; panelResult = PAUSE_TEXT
    await setPhase($, 'paused')
    await notify($, PAUSE_TEXT, true); $.ui.status(PAUSE_TEXT)
    await log($, `paused after ${chain.unattended} handoffs in a row`)
    return false
  }
  return true
}

async function arm($: EngineInterface, turnId: string | null, why: string) {
  if (chain!.phase !== 'gated') await log($, `trigger: ${why}, size ${await size($)}, line ${lineNow().line}`)
  armedTurn = turnId
  if (chain!.phase !== 'gated') { panelStep = -1; panelResult = null }
  await setPhase($, 'gated')
}

async function fail($: EngineInterface, text: string) {
  if (!counted) { chain!.unattended++; counted = true }
  panelResult = `auto handoff failed: ${text}`
  await setPhase($, 'failed')
  panelStep = -1
  await notify($, panelResult, true)
  $.ui.status(`auto handoff failed: ${text}`)
  await log($, `failed: ${text}`)
  await resendHeld($)
}

async function resendHeld($: EngineInterface) {
  const resend = held
  held = []
  for (const text of resend) {
    const m = text.match(/^\/(\S+)\s*([\s\S]*)$/)
    if (m) void $.command.run({ command: m[1]!, args: m[2] ?? '' }).catch(() => {})
    else void $.prompt.submit({ text }).catch(() => {})
    await log($, 'held prompt sent again')
  }
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
  requestAtTrigger = c.lastRequest
  answeredAtTrigger = c.answered !== false
  panelStep = 0; panelResult = null
  await setPhase($, 'rolling')
  await notify($, `auto handoff started: ${STEPS[0]}`)
  const args = fillTemplate(await template($, 'sections'), {
    priority: false, lastRequest: requestAtTrigger ?? '(none typed in this chat)',
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
  handoffTokens = n.tokens
  // AC-4 to AC-6: this handover's page and link, the one before it linked as previous.
  const prevLink = c.link ?? null
  const key = randomKey()
  const page = `${dir}/pages/${c.session}.html`
  c.pageKey = key
  c.link = viewerBase ? `${viewerBase}/${c.session.slice(0, 8)}-${key}` : `file://${page}`
  nextFor = prevLink && c.previous ? { page: `${dir}/pages/${c.previous}.html`, link: c.link } : null
  const facts = extractFacts(await $.session.messages(), ignoreFiles)
  const marked = markUnverified(await $.fs.read(path), n)
  for (const f of marked.marked) await log($, `unverified figure: ${f}`)
  const slot = insertAfterHeading(marked.text, factsBlock(facts, n, c.link))
  await $.fs.write(path, slot)
  await $.fs.write(page, renderPage(slot, { key, prev: prevLink, title: `Handover ${c.triggeredAt}` }))
    .catch(err => log($, `page not written (${err})`))
  panelStep = 1
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
      if (how === 'timeout') { lateClear = true; void cleared.then(() => { lateClear = false }) }
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
  panelStep = 2
  await setPhase($, 'seeding')
  if (nextFor) {
    const { page, link } = nextFor
    nextFor = null
    await $.fs.read(page).then(html => $.fs.write(page, addNext(html, link))).catch(() => log($, `previous page ${page} not found`))
  }
  // The mod's own record wins; the handover's Status line can only add priority, never drop it.
  const priority = (!!requestAtTrigger && !answeredAtTrigger) || lastRequestStatus(slot) === 'not answered'
  // The request the rollover judged, not one held since (those are sent again below).
  const args = fillTemplate(await template($, 'instructions'), { priority, lastRequest: requestAtTrigger ?? '' })
  await log($, `cleared; seed run (priority ${priority ? 'on' : 'off'})`)
  $.command.run({ command: 'resume-from-clear', args }).catch(err =>
    fail($, `the fresh chat did not start (${err}); the handover waits, type /resume-from-clear`))
  await setPhase($, 'idle')
  await resendHeld($)
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
    const root = await $.fs.read(`${dir}/${id}.root`).then(t => t.trim()).catch(() => id)
    const c = await $.fs.read(`${dir}/${root}.json`).then(t => JSON.parse(t) as Chain).catch(() => null)
    if (c?.session === id) chain = c
    chain ??= { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }
    // A reload mid handoff loses the in-memory flags and timers that would finish it, so the
    // phase would hold every typed prompt forever.
    if (['gated', 'rolling', 'clearing', 'seeding'].includes(chain.phase)) {
      await log($, `failed: the mod reloaded during ${chain.phase}`)
      await setPhase($, 'failed')
      $.ui.status('auto handoff failed: the mod reloaded mid handoff')
    }
    void startServer($)
    return started
  })

  on('session.end', async ($, e, next) => {
    const r = await next(e)
    // An owner's own /clear starts a new chain and gets no seed.
    if (active && e.reason === 'clear' && chain && chain.phase === 'failed' && lateClear) {
      // AC-7: the handoff's own clear, done after its 15 s timeout, is not the owner's /clear; the
      // chain and its failed count go on into the new chat.
      lateClear = false
      const id = await $.session.id().catch(() => '')
      if (id) { chain.previous = chain.session; chain.session = id; await save($) }
      pending = 0; awaitStart = false; exemptTurn = false; exemptNext = false
    } else if (active && e.reason === 'clear' && chain && chain.phase !== 'clearing') {
      chain = null
      const id = await $.session.id().catch(() => '')
      if (id) chain = { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }
      pending = 0; awaitStart = false; exemptTurn = false; exemptNext = false
    }
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    if (!active || !chain) return next(e)
    const typed = e.origin.kind === 'composer' || e.origin.kind === 'bridge'
    const owner = typed && !e.command && !e.text.startsWith('/')
    if (typed && ['gated', 'rolling', 'clearing', 'seeding'].includes(chain.phase)) {
      held.push(e.text)
      if (owner) { chain.unattended = 0; chain.lastRequest = e.text; chain.answered = false; await save($) }
      await log($, `prompt held during ${chain.phase}`)
      // AC-2: an interrupted gated turn that never reached turn.complete hands off here.
      if (chain.phase === 'gated' && !e.turnId) void startHandoff($)
      return { drop: HOLD_TEXT }
    }
    if (owner) {
      chain.unattended = 0
      chain.lastRequest = e.text
      chain.answered = false
      if (chain.phase === 'paused' || chain.phase === 'failed') {
        chain.phase = 'idle'; panelResult = null; $.ui.status(undefined)
        await writePanel($)
      }
      await save($)
    }
    if (EXEMPT.some(c => e.text === `/${c}` || e.text.startsWith(`/${c} `)) || EXEMPT.includes(e.command?.name ?? '')) {
      if (e.turnId) exemptNext = true
      else exemptTurn = true
    }
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
    if (exemptNext && e.turnId !== currentTurn) { exemptNext = false; exemptTurn = true }
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
      if (tokens != null) {
        chain.startTokens = tokens; awaitStart = false; await save($); await log($, `fresh chat starts at ${tokens}`)
        panelStep = STEPS.length; panelResult = `handed off \u00b7 ${k(handoffTokens)} -> ${k(tokens)}`
        await writePanel($)
        await notify($, `${panelResult} \u00b7 ${chain.link ?? ''}`)
      }
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
    // A gated turn was cut short, so it did not answer; any other turn ran to its end.
    if (!wasExempt && chain.phase !== 'gated' && chain.answered === false) { chain.answered = true; await save($) }
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
