import { expect, test } from 'claude-code/testing'
import { extractFacts, factsBlock, fillTemplate, insertAfterHeading, lastRequestStatus, markUnverified, type Numbers } from '../facts.ts'

// Spec 0063: the code that writes facts and numbers into the handover, without the engine.
const N: Numbers = { tokens: 60000, line: 50000, lineSource: 'threshold setting', start: 45000, unattended: 1 }
const bytes = (s: string) => new TextEncoder().encode(s).length
const uses = (...toolUses: unknown[]) => [{ toolUses }] as any

test('AC-4 files from Edit, Write and NotebookEdit, once each, minus ignoreFiles', async () => {
  const f = extractFacts(uses(
    { tool: 'Edit', input: { file_path: '/w/a.ts' } },
    { tool: 'Edit', input: { file_path: '/w/a.ts' } },
    { tool: 'Write', input: { file_path: '/w/dist/x.js' } },
    { tool: 'Write', input: { file_path: '/w/bun.lock' } },
    { tool: 'NotebookEdit', input: { notebook_path: '/w/n.ipynb' } },
    { tool: 'Read', input: { file_path: '/w/read.ts' } },
  ), '/w/dist/**, *.lock')
  expect(f.files).toEqual(['/w/a.ts', '/w/n.ipynb'])
})

test('AC-4 commits only from git commit output, subjects stripped of markdown', async () => {
  const f = extractFacts(uses(
    { tool: 'Bash', input: { command: 'git log' }, text: '[main 1111111] not a commit we made' },
    { tool: 'Bash', input: { command: 'git commit -m x' }, text: '[feat/x (root-commit) abcdef1] ## `fake` *heading*\n[main 2222222] feat: real' },
  ), '')
  expect(f.commits).toEqual(['abcdef1 fake heading', '2222222 feat: real'])
})

test('AC-4 issue and PR links from any tool output, once each', async () => {
  const f = extractFacts(uses(
    { tool: 'Bash', input: { command: 'gh' }, text: 'https://github.com/o/r/issues/3 and https://github.com/o/r/pull/4 https://github.com/o/r/issues/3' },
    { tool: 'Read', input: {}, text: 'https://github.com/o/r/blob/main/x https://github.com/o/r/discussions/5' },
  ), '')
  expect(f.links).toEqual(['https://github.com/o/r/issues/3', 'https://github.com/o/r/pull/4'])
})

test('AC-4 AC-5 the block holds numbers and stays under 2000 bytes with +N more', async () => {
  const many = (p: string) => Array.from({ length: 300 }, (_, i) => `${p}-${i}-ñandú-日本語`)
  const block = factsBlock({ files: many('/w/src/file'), commits: many('abc1234 subject'), links: many('https://github.com/o/r/issues') }, N, 'http://100.1.2.3:3846/S1')
  expect(bytes(block)).toBeLessThan(2000)
  expect(block.match(/^- \+\d+ more$/gm)?.length).toBe(3)
  expect(block).toContain('viewer: http://100.1.2.3:3846/S1')
  for (const s of ['- tokens at handoff: 60000', '- handoff line: 50000 (threshold setting)', '- starting size of this chat: 45000', '- handoffs since the owner last typed: 1']) expect(block).toContain(s)
})

test('AC-4 short lists are kept whole, empty ones say none, unknown start', async () => {
  const block = factsBlock({ files: ['/w/a.ts'], commits: [], links: [] }, { ...N, start: null })
  expect(block).toContain('Files edited or written:\n- /w/a.ts\nCommits:\n- none\nIssues and PRs:\n- none')
  expect(block).not.toContain('more')
  expect(block).not.toContain('viewer:')
  expect(block).toContain('- starting size of this chat: unknown')
})

test('AC-4 the block goes right after the first heading', async () => {
  expect(insertAfterHeading('intro\n# H\nNext: x', 'B')).toBe('intro\n# H\n\nB\nNext: x')
  expect(insertAfterHeading('no heading', 'B')).toBe('B\nno heading')
})

test('AC-5 unverified figures are marked only on context lines, outside code, numbers and fences', async () => {
  const slot = [
    '# H',
    'Context was 12% full at 1,234,567 tokens and 150k, see `99k` and run-200k.txt',
    'Context is 60k tokens, the line 50000, start 45000',
    'Built 5000 widgets',
    '```',
    'context 777k',
    '```',
    '## Handoff numbers',
    '- tokens 31337',
  ].join('\n')
  const r = markUnverified(slot, N)
  const out = r.text.split('\n')
  expect(out[1]).toBe('Context was 12% [unverified: not in Handoff numbers] full at 1,234,567 tokens [unverified: not in Handoff numbers] and 150k [unverified: not in Handoff numbers], see `99k` and run-200k.txt')
  expect(out[2]).toBe('Context is 60k tokens, the line 50000, start 45000')
  expect(out.slice(3).join('\n')).toBe(slot.split('\n').slice(3).join('\n'))
  expect(r.marked).toEqual(['12%', '1,234,567 tokens', '150k'])
  expect(markUnverified('Context is `ctx 99k more` now', N).text).toBe('Context is `ctx 99k more` now')
})

test('AC-6 the Status line under the last request section switches priority', async () => {
  expect(lastRequestStatus('# H\n## Last request from the owner\n> x\nStatus: not answered\n')).toBe('not answered')
  expect(lastRequestStatus('# H\n## Last request from the owner\n> x\n**Status:** Answered\n## Next\nStatus: not answered')).toBe('answered')
  expect(lastRequestStatus('# H\n## Last request from the owner\n> x\n## Next\nStatus: not answered')).toBeUndefined()
  expect(lastRequestStatus('# H\nStatus: not answered')).toBeUndefined()
})

test('AC-9 templates switch priority blocks and quote the last request as typed', async () => {
  const t = '{{#priority}}FIRST {{lastRequest}}{{/priority}}{{^priority}}GO ON{{/priority}}'
  expect(fillTemplate(t, { priority: true, lastRequest: "use $& and $' and $1" })).toBe("FIRST use $& and $' and $1")
  expect(fillTemplate(t, { priority: false, lastRequest: 'x' })).toBe('GO ON')
})
