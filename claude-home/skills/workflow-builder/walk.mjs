// Spec 0076 AC-5: walks a Workflow script for check.py. Prints one JSON object: the meta object (or why it is not
// a literal), each phase() title, each agent( call with its option keys and literal model, effort and phase, and
// the banned calls. Comments and strings are skipped, so a word in a prompt is never read as code.
// shortcut: a regex literal holding a quote would confuse the scanner; the templates use none.
import { readFileSync } from 'node:fs'

const src = readFileSync(process.argv[2], 'utf8')

// code: the source with every comment and string body blanked to spaces (newlines kept, so offsets and lines hold).
// Template literal ${...} parts stay code.
function blank(s) {
  const out = s.split('')
  const stack = [] // '`' for a template body, '{' for a brace inside a ${...}
  let i = 0
  const wipe = (a, b) => { for (let k = a; k < b; k++) if (out[k] !== '\n') out[k] = ' ' }
  while (i < s.length) {
    const c = s[i], top = stack[stack.length - 1]
    if (top === '`') {
      if (c === '\\') { wipe(i, i + 2); i += 2; continue }
      if (c === '`') { stack.pop(); i++; continue }
      if (c === '$' && s[i + 1] === '{') { stack.push('${'); i += 2; continue }
      wipe(i, i + 1); i++; continue
    }
    if (c === '/' && s[i + 1] === '/') { const e = s.indexOf('\n', i); const end = e < 0 ? s.length : e; wipe(i, end); i = end; continue }
    if (c === '/' && s[i + 1] === '*') { const e = s.indexOf('*/', i + 2); const end = e < 0 ? s.length : e + 2; wipe(i, end); i = end; continue }
    if (c === '"' || c === "'") {
      let j = i + 1
      while (j < s.length && s[j] !== c && s[j] !== '\n') j += s[j] === '\\' ? 2 : 1
      wipe(i + 1, j); i = j + 1; continue
    }
    if (c === '`') { stack.push('`'); i++; continue }
    if (c === '{') stack.push('{')
    if (c === '}') {
      const t = stack.pop()
      if (t === '${') { i++; continue } // back inside the template body
    }
    i++
  }
  return out.join('')
}

const code = blank(src)
const line = at => src.slice(0, at).split('\n').length

// the index just past the bracket that closes the one at `open`, read on blanked code
function close(open) {
  const pairs = { '(': ')', '{': '}', '[': ']' }
  const want = [pairs[code[open]]]
  for (let i = open + 1; i < code.length; i++) {
    const c = code[i]
    if (pairs[c]) want.push(pairs[c])
    else if (c === want[want.length - 1]) { want.pop(); if (!want.length) return i + 1 }
  }
  return -1
}

// top level pieces of src[a, b) split on commas at depth 0 (blanked code decides the depth)
function split(a, b) {
  const parts = []
  let depth = 0, start = a
  for (let i = a; i < b; i++) {
    const c = code[i]
    if ('({['.includes(c)) depth++
    else if (')}]'.includes(c)) depth--
    else if (c === ',' && depth === 0) { parts.push([start, i]); start = i + 1 }
  }
  if (code.slice(start, b).trim()) parts.push([start, b])
  return parts
}

const literal = (a, b) => {
  const t = src.slice(a, b).trim()
  return /^(['"])[^'"\\]*\1$/.test(t) ? t.slice(1, -1) : null
}

// keys of the object literal whose braces are src[a, b): key -> [valueStart, valueEnd]
function keys(a, b) {
  const found = {}
  for (const [s, e] of split(a + 1, b - 1)) {
    const m = /^\s*([A-Za-z_$][\w$]*)\s*(:?)/.exec(code.slice(s, e))
    if (!m) continue
    found[m[1]] = m[2] ? [s + m.index + m[0].length, e] : null
  }
  return found
}

const result = { meta: null, metaError: null, phases: [], agents: [], banned: [] }

// meta: a pure literal, read by this parser and never evaluated. A vm eval of it used to run code from the script
// being checked (PR 176 review: a regex literal holding a quote blinded blank() and let a call through).
// Strings, numbers, true, false, null, arrays and objects with plain or quoted keys; anything else is refused.
function literalAt(s, i) {
  const fail = () => { throw new Error('not a literal') }
  const ws = () => {
    for (;;) {
      while (/\s/.test(s[i] || '')) i++
      if (s.startsWith('//', i)) { const e = s.indexOf('\n', i); i = e < 0 ? s.length : e }
      else if (s.startsWith('/*', i)) { const e = s.indexOf('*/', i + 2); if (e < 0) fail(); i = e + 2 }
      else return
    }
  }
  const str = () => {
    const q = s[i++]
    let out = ''
    while (s[i] !== q) {
      if (i >= s.length || s[i] === '\n') fail()
      if (s[i] === '\\') { const c = s[i + 1]; out += { n: '\n', t: '\t', r: '\r' }[c] ?? c; i += 2 } else out += s[i++]
    }
    i++
    return out
  }
  const value = () => {
    ws()
    const c = s[i]
    if (c === "'" || c === '"') return str()
    if (c === '{') {
      i++
      const obj = {}
      for (ws(); s[i] !== '}'; ws()) {
        let key
        if (s[i] === "'" || s[i] === '"') key = str()
        else { const m = /^[A-Za-z_$][\w$]*/.exec(s.slice(i)); if (!m) fail(); key = m[0]; i += key.length }
        ws()
        if (s[i++] !== ':') fail()
        obj[key] = value()
        ws()
        if (s[i] === ',') i++
        else if (s[i] !== '}') fail()
      }
      i++
      return obj
    }
    if (c === '[') {
      i++
      const arr = []
      for (ws(); s[i] !== ']'; ws()) {
        arr.push(value())
        ws()
        if (s[i] === ',') i++
        else if (s[i] !== ']') fail()
      }
      i++
      return arr
    }
    const m = /^(-?\d+(\.\d+)?|true|false|null)(?![\w$])/.exec(s.slice(i))
    if (!m) fail()
    i += m[0].length
    return JSON.parse(m[0])
  }
  return value()
}

const mm = /export\s+const\s+meta\s*=\s*\{/.exec(code)
if (!mm) result.metaError = 'no `export const meta = {...}`'
else {
  try { result.meta = literalAt(src, mm.index + mm[0].length - 1) } catch (e) { result.metaError = 'meta is not a literal' }
}

// phase('...') calls and agent( calls, in source order
const calls = [...code.matchAll(/(?<![\w$.])(phase|agent)\s*\(/g)]
let current = null
for (const m of calls) {
  const open = m.index + m[0].length - 1, end = close(open)
  if (end < 0) continue
  const args = split(open + 1, end - 1)
  if (m[1] === 'phase') {
    current = args.length ? literal(...args[0]) : null
    if (current !== null) result.phases.push(current)
    continue
  }
  const last = args[args.length - 1]
  const opts = last && code.slice(...last).trim().startsWith('{') ? (() => {
    const s = last[0] + code.slice(...last).indexOf('{')
    return keys(s, close(s))
  })() : {}
  const val = k => (opts[k] ? literal(...opts[k]) : null)
  result.agents.push({ line: line(m.index), keys: Object.keys(opts), model: val('model'), effort: val('effort'),
                       phase: val('phase') ?? current })
}

const banned = [[/\bDate\s*\.\s*now\s*\(/g, 'Date.now('], [/\bMath\s*\.\s*random\s*\(/g, 'Math.random('],
                [/\bnew\s+Date\s*\(\s*\)/g, 'new Date()'], [/(?<![\w$.])import\s*\(/g, 'import(']]
for (const [re, name] of banned) for (const m of code.matchAll(re)) result.banned.push({ name, line: line(m.index) })

console.log(JSON.stringify(result))
