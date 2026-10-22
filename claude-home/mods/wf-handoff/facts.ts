// Spec 0063 AC-4, AC-5, AC-9: what code (never the model) adds to the handover. The idea of
// facts pulled from the transcript and figures marked unverified comes from
// alexknowshtml/claude-auto-handoff 0.8.6 (MIT, credited in docs/NOTICE.md).

export type Msg = { toolUses?: readonly { tool: string; input: Record<string, unknown>; text?: string; isError?: boolean }[] }

export type Numbers = {
  tokens: number
  line: number
  lineSource: string
  start: number | null
  unattended: number
}

const FACTS_BUDGET = 2000

const globRe = (glob: string) =>
  new RegExp('^' + glob.trim().replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*\*/g, '\u0000').replace(/\*/g, '[^/]*').replace(/\u0000/g, '.*').replace(/\?/g, '.') + '$')

// Commit subjects come from `git log`: one line, no control characters or markdown markers,
// at most 100 characters, so a subject cannot pose as a section of the handover.
const clean = (s: string) => s.replace(/[\u0000-\u001f\u007f#>`*_[\]]/g, '').trim().slice(0, 100)

// Links come only from Bash calls that ran gh or git push, where a real issue or PR link shows:
// a link read from a test fixture (a Read, a grep, a test run) was listed as a PR once.
const LINK_SOURCE = /(^|[\s;&|(])(gh(?=\s|$)|git\s+(?:-C\s+\S+\s+)?push\b)/

export function extractFacts(messages: readonly Msg[], ignoreFiles: string, gitLog = '') {
  const ignore = ignoreFiles.split(',').filter(g => g.trim()).map(globRe)
  const files: string[] = [], commits: string[] = [], links: string[] = []
  const add = (list: string[], v: string) => { if (!list.includes(v)) list.push(v) }
  for (const m of messages) for (const u of m.toolUses ?? []) {
    if (!u.isError && (u.tool === 'Edit' || u.tool === 'Write' || u.tool === 'NotebookEdit')) {
      const p = String(u.input.file_path ?? u.input.notebook_path ?? '')
      if (p && !ignore.some(r => r.test(p) || r.test(p.split('/').pop()!))) add(files, p)
    }
    if (u.tool !== 'Bash' || !LINK_SOURCE.test(String(u.input.command ?? ''))) continue
    for (const l of (u.text ?? '').matchAll(/https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/(?:issues|pull)\/\d+/g)) add(links, l[0])
  }
  // `git log --format='%h %s'` since the chat started, newest first
  for (const c of gitLog.matchAll(/^([0-9a-f]{7,40}) (.+)$/gm)) add(commits, `${c[1]} ${clean(c[2]!)}`)
  return { files, commits, links }
}

// One block, under FACTS_BUDGET bytes: lists cut short end in "+N more" so the 7,000 byte
// cut of handover-start.sh still keeps the rollover's own next actions.
export function factsBlock(facts: ReturnType<typeof extractFacts>, n: Numbers, viewer?: string) {
  const numbers = [
    '## Handoff numbers',
    `- tokens at handoff: ${n.tokens}`,
    `- handoff line: ${n.line} (${n.lineSource})`,
    `- starting size of this chat: ${n.start ?? 'unknown'}`,
    `- handoffs since the owner last typed: ${n.unattended}`,
  ].join('\n')
  const lists: [string, string[]][] = [
    ['Files edited or written', facts.files],
    ['Commits', facts.commits],
    ['Issues and PRs', facts.links],
  ]
  const frame = (bodies: string[][]) => [
    '## Handoff facts',
    '(pulled by the wf-handoff mod from this chat\'s tool calls, their output and git log; the model did not write this list)',
    ...(viewer ? [`viewer: ${viewer}`] : []),
    ...lists.map(([title], i) => [`${title}:`, ...bodies[i]!].join('\n')),
    '',
    numbers,
    '',
  ].join('\n')
  // This used to count only the heading, viewer and numbers plus a guessed 120, so the note,
  // titles, "- none" and "+N more" lines pushed the block past the budget (2075 bytes in
  // verify). Now the room is the budget minus the real frame, with each list's worst case
  // "+N more" line reserved, measured in UTF-8 bytes.
  const bytes = (s: string) => new TextEncoder().encode(s).length
  let room = FACTS_BUDGET - 1 - bytes(frame(lists.map(([, l]) => [l.length ? `- +${l.length} more` : '- none'])))
  return frame(lists.map(([, list]) => {
    if (!list.length) return ['- none']
    const kept: string[] = []
    for (const v of list) {
      const line = `- ${v}`
      if (bytes(line) + 1 > room) break
      kept.push(line); room -= bytes(line) + 1
    }
    const more = list.length - kept.length
    return [...kept, ...(more ? [`- +${more} more`] : [])]
  }))
}

export function insertAfterHeading(slot: string, block: string) {
  const lines = slot.split('\n')
  const i = lines.findIndex(l => /^#/.test(l))
  if (i < 0) return `${block}\n${slot}`
  return [...lines.slice(0, i + 1), '', block, ...lines.slice(i + 1)].join('\n')
}

const UNVERIFIED = ' [unverified: not in Handoff numbers]'

// AC-5: a token figure ("N tokens", "Nk") on a context line that the numbers block does not hold
// is marked. Percentages and bare 4 digit numbers were marked too, and all 9 marks in the audit
// were true facts; a quoted owner line (`> ...`) holds the owner's own words and is never marked.
export function markUnverified(slot: string, n: Numbers) {
  const known = [n.tokens, n.line, n.start].filter((v): v is number => v != null)
  const marked: string[] = []
  let fence = false, inNumbers = false
  const out = slot.split('\n').map(line => {
    if (/^\s*```/.test(line)) { fence = !fence; return line }
    if (/^#/.test(line)) inNumbers = /^## Handoff numbers/.test(line)
    if (fence || inNumbers || /^\s*>/.test(line) || !/context|tokens?\b/i.test(line)) return line
    return line.split(/(`[^`]*`)/).map(part => part.startsWith('`') ? part : part.replace(
      /(^|[\s(])([^\s()]*?)(\d[\d,]*(?:\.\d+)?)(\s*k\b|\s*tokens\b)(?=[\s.,;:)]|$)/gi,
      (all, pre, lead, num, unit) => {
        if (lead) return all // part of a file name, path or word
        const isK = /k/i.test(unit)
        const v = parseFloat(num.replace(/,/g, '')) * (isK ? 1000 : 1)
        if (known.some(k => isK ? Math.abs(k - v) < 1000 : k === v)) return all
        marked.push(`${num}${unit}`)
        return `${pre}${num}${unit}${UNVERIFIED}`
      })).join('')
  })
  return { text: out.join('\n'), marked }
}

// AC-6: the priority switch reads the Status line under "## Last request from the owner".
export function lastRequestStatus(slot: string): 'answered' | 'not answered' | undefined {
  const m = slot.match(/^## Last request from the owner[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/m)
  const s = m?.[1]?.match(/^\s*\**Status:?\**:?\s*(not answered|answered)/im)
  return s ? (s[1]!.toLowerCase() as 'answered' | 'not answered') : undefined
}

export function fillTemplate(text: string, vars: { priority: boolean; lastRequest: string; transcript?: string | null }) {
  const path = vars.transcript ?? ''
  return text
    .replace(/\{\{#priority\}\}([\s\S]*?)\{\{\/priority\}\}/g, (_, b) => (vars.priority ? b : ''))
    .replace(/\{\{\^priority\}\}([\s\S]*?)\{\{\/priority\}\}/g, (_, b) => (vars.priority ? '' : b))
    // the chat's own log when the mod found it, else the block drops and the skill finds it its own way
    .replace(/\{\{#transcript\}\}([\s\S]*?)\{\{\/transcript\}\}/g, (_, b) => (path ? b : ''))
    .replace(/\{\{\^transcript\}\}([\s\S]*?)\{\{\/transcript\}\}/g, (_, b) => (path ? '' : b))
    .replace(/\{\{transcript\}\}/g, () => path)
    // A function, not a string: a string replacement reads "$&" and "$'" in the owner's text as
    // patterns and garbled the request in verify.
    .replace(/\{\{lastRequest\}\}/g, () => vars.lastRequest)
    .trim()
}
