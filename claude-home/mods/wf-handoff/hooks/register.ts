import type { EngineInterface, PluginOptions, Register } from 'claude-code'
import { extractFacts, factsBlock, fillTemplate, insertAfterHeading, lastRequestStatus, markUnverified, notLive, notLiveNotice, type Numbers } from '../facts.ts'
import { addNext, renderPage } from '../pages.ts'

type Phase = 'idle' | 'gated' | 'rolling' | 'clearing' | 'seeding' | 'paused' | 'failed'
type Chain = {
  root: string; session: string; previous: string | null; startTokens: number | null; unattended: number
  triggeredAt: string | null; phase: Phase; lastRequest: string | null; link?: string; pageKey?: string
  answered?: boolean // false from an owner prompt until a turn ends without the gate
  // /auto-handoff off: this chat never hands off on its own. Copied from the folder's off file
  // (offFile) at every chat start and clear, so the chain alone no longer decides it.
  off?: boolean
  // the line in force at the last save, for the chip-dash band (it reads this file, no shared code)
  line?: number
  // when this chat started (ISO): the handover's commits are `git log --since` it
  startedAt?: string
}

const GATE_TEXT = 'context is at the handoff line; finish this turn in words, the handoff starts at the end of it'
const HOLD_TEXT = 'held for the handoff; it is sent for you, clear the box'
const PAUSE_TEXT = 'auto handoff paused: type anything to resume'
const EXEMPT = ['rollover', 'save-and-clear', 'handoff']
const CLEAR_TIMEOUT_MS = 15000
// shortcut: the log is cut to its newer half past this size; one log is shared by every chat
const LOG_MAX = 256000
// Spec 0064 AC-1: the steps the chip-dash band draws from panel.json.
const STEPS = ['writing the handover', 'clearing', 'starting the fresh chat']
const STICKY_TOAST_MS = 30000
// The gate used to refuse the very next tool call, so a promised step (a file save, a send to the
// phone, a note to a helper) stopped halfway: a gated turn gets this many more calls first, enough
// for a write, a send and its check.
const GRACE_CALLS = 3
// Past the line by this much every tool call is refused, an owner's turn and the grace included.
const HARD_MARGIN = 20000
// A handoff used to stop a running helper agent, which was then relaunched from zero: it waits for
// this chat's background agents first, checking every AGENT_POLL_MS, at most AGENT_WAIT_MS.
const AGENT_WAIT_MS = 15 * 60000
const AGENT_POLL_MS = 5000

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
let transcript: string | null = null // the handed off chat's own log, found once per handoff
let notLiveAtHandoff: string[] = [] // open PRs and branches not on main at the handoff
let folder = '' // realpath of the folder this chat started in
let ownerNext = false // an owner message typed while idle: the next turn starts with it
let ownerTurn = false // this turn started with a fresh owner message: never gated below HARD_MARGIN
let graceLeft = 0
let waitingAgents = false
// session.start waits on the other start hooks (MCP servers connecting, tens of seconds after
// `claude -c`); an /auto-handoff typed in that window used to find no chain and say the chat
// does not run the handoff (2026-10-22).
let startDone = false
let startWaiters: (() => void)[] = []
const startFinished = () => { startDone = true; startWaiters.splice(0).forEach(f => f()) }

// The rollover skill took "the newest log in the project folder" as this chat's transcript: a
// background agent's newer log was named instead once, and the search plus its 27k character
// listing cost a model round trip in each rollover and another in the fresh chat.
async function transcriptOf($: EngineInterface, id: string) {
  const base = `${home}/.claude/projects`
  for (const d of await $.fs.list(base).catch(() => [])) {
    const p = `${base}/${d.name}/${id}.jsonl`
    if (await $.fs.stat(p).catch(() => null)) return p
  }
  return null
}

async function slotCmd($: EngineInterface) {
  const cwd = await $.session.cwd()
  return $.process.run(
    [`${home}/.claude/skills/jjstack/bin/jjstack-rollover-slot`, '--cwd', cwd, 'status', '--max-age-days', '1'],
    { timeoutMs: 2000 },
  ).catch(() => ({ exitCode: 1, stdout: '' }))
}

// Off used to live only on the chain of the chat it was typed in, so a new, resumed, forked or
// owner cleared chat in the same folder got a fresh chain and handed off at the line anyway
// (row 95, 2026-10-22). It is now one file per folder: 'off' or 'on', last word wins.
const offFile = () => `${dir}/off-${encodeURIComponent(folder)}`
const folderOff = async ($: EngineInterface) => (await $.fs.read(offFile()).catch(() => '')).trim() === 'off'

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
  chain.line = lineNow().line
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

// AC-3: a toast only where no band draws the panel: chip-dash not loaded, or a surface with no band
// (the host raises the band on the terminal and the desktop only).
async function notify($: EngineInterface, text: string, sticky = false) {
  const surfaces = await $.session.surfaces().catch(() => [] as readonly string[])
  const dash = surfaces.some(s => s !== 'terminal' && s !== 'desktop') ? null
    : await $.state.get({ plugin: 'chip-dash', key: 'facts' } as any).catch(() => null)
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
  if (!chain || chain.off || exemptTurn || (chain.phase !== 'idle' && chain.phase !== 'gated')) return false
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
  if (chain!.phase !== 'gated') { panelStep = -1; panelResult = null; graceLeft = GRACE_CALLS }
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

async function agentsRunning($: EngineInterface) {
  const list = await $.agent.list().catch(() => [])
  return list.filter(a => a.status === 'pending' || a.status === 'running' || a.status === 'waiting').length
}

// Every caller is in the gated phase; the wait runs off the hook, so turns and prompts go on
// meanwhile (held, as in any gated phase), and an owner /clear during it drops the handoff.
async function startHandoff($: EngineInterface) {
  if (waitingAgents) return
  const busy = await agentsRunning($)
  if (!busy) return beginHandoff($)
  waitingAgents = true
  await log($, `waiting for ${busy} background agent(s) before the handoff`)
  void (async () => {
    const until = (await $.clock.now()) + AGENT_WAIT_MS
    while ((await agentsRunning($)) && (await $.clock.now()) < until) await $.clock.sleep(AGENT_POLL_MS)
    waitingAgents = false
    if (chain?.phase !== 'gated') return
    await log($, (await agentsRunning($)) ? `agents still running after ${AGENT_WAIT_MS / 60000} min; handoff starts` : 'background agents done; handoff starts')
    await beginHandoff($)
  })()
}

async function beginHandoff($: EngineInterface) {
  const c = chain!
  c.triggeredAt = new Date(await $.clock.now()).toISOString()
  rollResolved = false
  counted = false
  requestAtTrigger = c.lastRequest
  answeredAtTrigger = c.answered !== false
  panelStep = 0; panelResult = null
  await setPhase($, 'rolling')
  await notify($, `auto handoff started: ${STEPS[0]}`)
  transcript = await transcriptOf($, c.session)
  const args = fillTemplate(await template($, 'sections'), {
    priority: false, lastRequest: requestAtTrigger ?? '(none typed in this chat)', transcript,
  })
  await log($, `rollover started${transcript ? '' : ' (transcript not found)'}`)
  // Probe P1: slash commands go through $.command.run (prompt.submit refuses them); P6: it
  // resolves when the rollover turn starts, so its end is the next main turn.complete.
  $.command.run({ command: 'rollover', args }).then(
    () => { rollResolved = true },
    err => fail($, `the rollover did not start (${err})`),
  )
}

// Every repo this chat touched: its folder plus each edited file's folder, one per git repo
// (a worktree shares its repo's common dir). The chat that started in ~/.claude, no repo, edited
// the claude-config plan, so its own folder alone would have found nothing (2026-10-22).
async function notLiveNow($: EngineInterface, files: string[]) {
  const run = (argv: string[]) => $.process.run(argv, { timeoutMs: 10000 }).catch(() => null)
  const seen = new Set<string>()
  const out: string[] = []
  for (const d of [...new Set([await $.session.cwd(), ...files.map(f => f.replace(/\/[^/]*$/, '') || '/')])].slice(0, 20)) {
    const r = await run(['git', '-C', d, 'rev-parse', '--path-format=absolute', '--git-common-dir'])
    const common = r?.exitCode === 0 ? r.stdout.trim() : ''
    if (!common || seen.has(common)) continue
    seen.add(common)
    // gh has no -C and finds its repo from the folder it runs in; `env -C` sets that folder
    const gh = await run(['env', '-C', d, 'gh', 'pr', 'list', '--author', '@me', '--state', 'open', '--json', 'number,title,url,isDraft', '--limit', '20'])
    const br = await run(['git', '-C', d, 'branch', '--no-merged', 'origin/HEAD', '--format=%(refname:short) %(upstream:track)'])
    out.push(...notLive(d, gh?.exitCode === 0 ? gh.stdout : null, br?.exitCode === 0 ? br.stdout : null))
  }
  return out
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
  // Commits come from git, not from commit output: `git commit -q` prints none and an amend
  // printed a sha that no longer exists ("Commits: none" after 3 amends).
  const gitLog = c.startedAt
    ? await $.process.run(['git', '-C', await $.session.cwd(), 'log', `--since=${c.startedAt}`, '-n', '30', '--format=%h %s'], { timeoutMs: 5000 }).catch(() => null)
    : null
  const facts = extractFacts(await $.session.messages(), ignoreFiles, gitLog?.exitCode === 0 ? gitLog.stdout : '')
  notLiveAtHandoff = await notLiveNow($, facts.files)
  const marked = markUnverified(await $.fs.read(path), n)
  for (const f of marked.marked) await log($, `unverified figure: ${f}`)
  const slot = insertAfterHeading(marked.text, factsBlock(facts, n, c.link, notLiveAtHandoff))
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
  c.startedAt = new Date(await $.clock.now()).toISOString()
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
  // the real path: one fresh chat in six spent 11 s listing logs to find it. `<previous transcript>` is the
  // placeholder of the instructions copies written before {{transcript}} existed.
  const filled = fillTemplate(await template($, 'instructions'), { priority, lastRequest: requestAtTrigger ?? '', transcript })
  const notice = notLiveNotice(notLiveAtHandoff)
  const args = [transcript ? filled.split('<previous transcript>').join(transcript) : filled, notice].filter(Boolean).join('\n\n')
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
    await $.command.register({ name: 'auto-handoff', description: 'Auto handoff for chats in this folder: on, off, or no word to see it' })
    home = (await $.env.get('HOME')) ?? ''
    dir = `${home}/.claude/state/auto-handoff`
    active = e.isInteractive && !(await $.env.get('WF_RUN')) && !(await $.env.get('TM_WORKER_NAME'))
      && (await $.env.get('AUTO_HANDOFF_DISABLE')) !== '1'
    if (!active) { startFinished(); return started }
    const t = Number(await $.env.get('AUTO_HANDOFF_TOKENS'))
    envTokens = t > 0 ? t : null
    for (const name of ['sections', 'instructions']) {
      const own = `${home}/.claude/auto-handoff/${name}.md`
      if ((await $.fs.read(own).catch(() => null)) === null)
        await $.fs.write(own, await $.fs.read(`${$.plugin.root}/templates/${name}.md`)).catch(() => {})
    }
    // the start folder, not session.cwd later (that follows a Bash cd); a link such as
    // ~/claude-config resolves to the same folder as its target
    const r = await $.process.run(['realpath', '--', e.cwd], { timeoutMs: 2000 }).catch(() => null)
    folder = (r?.exitCode === 0 && r.stdout.trim()) || e.cwd
    const id = await $.session.id()
    // A reload of the module (settings change) keeps the chain from its state file.
    const root = await $.fs.read(`${dir}/${id}.root`).then(t => t.trim()).catch(() => id)
    const c = await $.fs.read(`${dir}/${root}.json`).then(t => JSON.parse(t) as Chain).catch(() => null)
    chain = c?.session === id ? c : { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }
    if (await folderOff($)) chain.off = true
    chain.startedAt ??= new Date(await $.clock.now()).toISOString()
    // A reload mid handoff loses the in-memory flags and timers that would finish it, so the
    // phase would hold every typed prompt forever.
    if (['gated', 'rolling', 'clearing', 'seeding'].includes(chain.phase)) {
      await log($, `failed: the mod reloaded during ${chain.phase}`)
      await setPhase($, 'failed')
      $.ui.status('auto handoff failed: the mod reloaded mid handoff')
    }
    // the band reads on/off and the line from this file from the chat's first tick
    else await save($)
    startFinished()
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
      // An owner's /clear used to drop the off typed before it; the folder's off holds for every clear.
      const off = await folderOff($)
      chain = null
      const id = await $.session.id().catch(() => '')
      if (id) chain = { root: id, session: id, previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null, startedAt: new Date(await $.clock.now()).toISOString(), ...(off ? { off } : {}) }
      pending = 0; awaitStart = false; exemptTurn = false; exemptNext = false
      await save($)
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
      // Gating the turn that answers it left the owner's newest message unanswered (audit fix 4)
      if (!e.turnId) ownerNext = true
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
      const hard = (await size($)) >= lineNow().line + HARD_MARGIN
      // an owner's turn runs on and hands off at its end, unless it reaches the hard margin
      if (hard || !ownerTurn) {
        await arm($, currentTurn, `tool call ${e.tool} past the line`)
        if (hard || graceLeft <= 0) {
          await log($, `refused ${e.tool}`)
          return { deny: GATE_TEXT }
        }
        graceLeft--
        await log($, `allowed ${e.tool} at the gate (${graceLeft} more)`)
      }
    }
    const r = await next(e)
    pending += r.text?.length ?? 0
    return r
  })

  on('turn.step', async function* ($, e, next) {
    if (!active || e.agentId || !chain) return yield* next(e)
    if (exemptNext && e.turnId !== currentTurn) { exemptNext = false; exemptTurn = true }
    if (e.turnId !== currentTurn) { ownerTurn = ownerNext; ownerNext = false }
    currentTurn = e.turnId
    // AC-2 fallback: a gated turn ended without turn.complete (Esc); the next step hands off.
    if (chain.phase === 'gated' && armedTurn !== e.turnId) {
      void startHandoff($)
      return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
    }
    if (chain.phase === 'idle' && !ownerTurn && (await crossed($))) {
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
    ownerTurn = false
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
    $.clock.after(1500, () => { void $.command.run({ command: 'clear', args: '' }).catch(() => {}) })
    return { text: `Handover found at ${r.stdout.trim()}; clearing in 1.5 s, then it loads.` }
  })

  // A chat that is not for coding fills fast and drifts less, so the owner turns the handoff off
  // there; the chip-dash band shows the state from the chain file save() writes.
  on('command.run', { command: 'auto-handoff' }, async ($, e) => {
    if (!startDone) {
      await new Promise<void>(resolve => { startWaiters.push(resolve); $.clock.after(60000, resolve) })
      if (!startDone) return { text: 'auto handoff is still starting (the chat start has not finished); try /auto-handoff again in a moment' }
    }
    // no chain: session.start found the chat inactive and made none
    if (!chain) return { text: 'auto handoff does not run in this chat (not interactive, a wf or worker chat, or AUTO_HANDOFF_DISABLE=1)' }
    const word = e.args.trim().toLowerCase()
    if (word !== '' && word !== 'on' && word !== 'off') return { text: `use /auto-handoff on, /auto-handoff off, or /auto-handoff alone to see it (got "${e.args.trim()}")` }
    if (word) {
      chain.off = word === 'off'
      await save($)
      await $.fs.write(offFile(), `${word}\n`).catch(() => {})
      await log($, `auto handoff ${word} for this chat and later chats in ${folder}`)
    }
    return { text: chain.off
      ? `auto handoff is off for this chat and every later chat started in ${folder}; /auto-handoff on turns it back on`
      : `auto handoff is on: this chat hands off at ${k(lineNow().line)} tokens (now ${k(await size($))})` }
  })
}
