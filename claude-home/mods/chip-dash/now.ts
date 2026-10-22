// Spec 0071: the Now view's two readers, as pure parsing. register.tsx reads the catch file and runs the one gh call.
import type { WfDashOwed, WfDashPr, WfDashPrs } from './types/index.d.ts'

// AC-3: every open PR you opened, newest update first, with its last commit's check rollup, in one call (probe P1)
export const PR_QUERY = 'query { search(query: "is:pr is:open author:@me sort:updated-desc", type: ISSUE, first: 20) { issueCount nodes { ... on PullRequest { number title isDraft url repository { name } commits(last: 1) { nodes { commit { statusCheckRollup { state } } } } } } } }'
export const prArgv = () => ['gh', 'api', 'graphql', '-f', `query=${PR_QUERY}`]

// GitHub's check rollup in one word. No rollup is none; a state GitHub does not document is ?, never a guessed word.
export function checksWord(rollup: unknown): string {
  if (rollup == null) return 'none'
  const s = (rollup as { state?: unknown }).state
  if (s === 'SUCCESS') return 'ok'
  if (s === 'FAILURE' || s === 'ERROR') return 'failing'
  if (s === 'PENDING' || s === 'EXPECTED') return 'pending'
  return '?'
}

// The search's stdout as PRs and their total; null when it is not the answer's shape (a failed call, never "no PRs")
export function parsePrs(stdout: string): WfDashPrs | null {
  let d: any
  try { d = JSON.parse(stdout) } catch { return null }
  const s = d?.data?.search
  if (!s || typeof s.issueCount !== 'number' || !Array.isArray(s.nodes)) return null
  const prs = s.nodes.filter((n: any) => n && typeof n.number === 'number').map((n: any): WfDashPr => ({
    repo: String(n.repository?.name ?? '?'),
    number: n.number,
    title: String(n.title ?? ''),
    draft: n.isDraft === true,
    url: String(n.url ?? ''),
    checks: checksWord(n.commits?.nodes?.[0]?.commit?.statusCheckRollup),
  }))
  return { total: s.issueCount, prs }
}

// AC-2: the catch file's text. One that does not parse, or has no `owed` list, is unknown (`owed ?`), never nothing owed.
export function parseOwed(raw: string): WfDashOwed {
  let d: any
  try { d = JSON.parse(raw) } catch (err: any) { return { installed: true, lines: null, error: String(err?.message ?? err) } }
  if (!Array.isArray(d?.owed)) return { installed: true, lines: null, error: 'the file has no owed list' }
  return { installed: true, lines: d.owed.map(String), error: null }
}
