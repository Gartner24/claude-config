// Spec 0064 AC-4: one readable page per handover, the chain linked in order. The idea of a
// page per brief comes from alexknowshtml/claude-auto-handoff (MIT, credited in docs/NOTICE.md);
// written fresh here. Every piece of slot text is escaped: the handover is model and tool text.

const NEXT = '<!--next-->'

export const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')

// A link is ours (http on the viewer address, or the file path), but it is escaped like the rest.
const a = (href: string, text: string) => `<a href="${esc(href)}">${esc(text)}</a>`

export function renderPage(slot: string, p: { key: string; title: string; prev: string | null }) {
  const body = slot.split('\n').map(line => {
    const h = line.match(/^(#{1,3}) (.*)$/)
    return h ? `<h${h[1]!.length}>${esc(h[2]!)}</h${h[1]!.length}>` : `<p>${esc(line) || '&nbsp;'}</p>`
  }).join('\n')
  return [
    '<!doctype html>',
    '<html lang="en"><head><meta charset="utf-8">',
    `<meta name="wf-handoff-key" content="${esc(p.key)}">`,
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${esc(p.title)}</title>`,
    '<style>body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:1rem auto;padding:0 1rem}p{margin:0;white-space:pre-wrap}nav{display:flex;gap:1.5rem;margin:1rem 0}</style>',
    '</head><body>',
    `<nav>${p.prev ? a(p.prev, 'previous handover') : '<span>first handover of this chain</span>'}${NEXT}</nav>`,
    body,
    '</body></html>',
    '',
  ].join('\n')
}

// At seed time the page before gets its next link; a page that already has one keeps it.
export function addNext(html: string, link: string) {
  return html.replace(NEXT, a(link, 'next handover'))
}
