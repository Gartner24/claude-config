#!/usr/bin/env node
// Context monitor (spec 0037), derived from get-shit-done-cc's gsd-context-monitor.js (MIT).
// PostToolUse hook: reads the session transcript after each tool call and warns the model,
// through additionalContext, as the session's context grows.
//
// The gsd version read a bridge file only gsd's own status line writes, so with jjstack's
// status line (or `wf auto bar`) it never fired, and its comment and code named different
// numbers. This one reads the transcript, and `--test` fails when the numbers drift.
//
// Thresholds (tokens used):
//   WARN_TOKENS          150000   ~/.claude/CLAUDE.md Context: past ~150k, finish the step, /rollover
//   AUTOCOMPACT_TOKENS   700000   settings.json autoCompactWindow
//   CRITICAL_TOKENS      650000   50k before autocompact

const fs = require('fs');
const os = require('os');
const path = require('path');

const WARN_TOKENS = 150000;
const AUTOCOMPACT_TOKENS = 700000;
const CRITICAL_TOKENS = AUTOCOMPACT_TOKENS - 50000;
const WARN_REPEAT = 100000; // a further WARNING at 250k, 350k, ... below CRITICAL
const TAIL_BYTES = 256 * 1024;

function usedTokens(transcriptPath) {
  const fd = fs.openSync(transcriptPath, 'r');
  try {
    const size = fs.fstatSync(fd).size;
    const len = Math.min(size, TAIL_BYTES);
    const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, size - len);
    const lines = buf.toString('utf8').split('\n');
    // Newest first. A line that does not parse is skipped, not fatal: the first line of the
    // window is usually cut, and the last may still be mid write.
    for (let i = lines.length - 1; i >= 0; i--) {
      let entry;
      try { entry = JSON.parse(lines[i]); } catch (e) { continue; }
      if (!entry || entry.type !== 'assistant' || entry.isSidechain === true) continue;
      const u = entry.message && entry.message.usage;
      if (!u) continue;
      return (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0);
    }
    return null;
  } finally {
    fs.closeSync(fd);
  }
}

// The highest mark reached: 0, 150k, 250k, ..., 550k, then CRITICAL_TOKENS.
function markFor(used) {
  if (used >= CRITICAL_TOKENS) return CRITICAL_TOKENS;
  if (used < WARN_TOKENS) return 0;
  return WARN_TOKENS + Math.floor((used - WARN_TOKENS) / WARN_REPEAT) * WARN_REPEAT;
}

function messageFor(used) {
  const k = Math.floor(used / 1000);
  if (used >= CRITICAL_TOKENS) {
    return `Context: ${k}k tokens used; autocompact (lossy) runs at ${AUTOCOMPACT_TOKENS / 1000}k. ` +
      'Do not start new work: finish this step and `/rollover` now.';
  }
  return `Context: ${k}k tokens used. Rule (\`~/.claude/CLAUDE.md\` Context): finish the current step, ` +
    'then `/rollover` mid feature or `/save-and-clear` at a boundary.';
}

function main(input) {
  if (process.env.WF_RUN) return;
  try {
    const data = JSON.parse(input);
    const sessionId = data.session_id;
    // session_id builds a path in the temp dir; a separator or .. could escape it.
    if (!sessionId || /[/\\]|\.\./.test(sessionId) || !data.transcript_path) return;
    const used = usedTokens(data.transcript_path);
    if (used === null) return;
    const mark = markFor(used);
    if (mark === 0) return;
    const statePath = path.join(os.tmpdir(), `context-monitor-${sessionId}.json`);
    let last = 0;
    try { last = JSON.parse(fs.readFileSync(statePath, 'utf8')).last || 0; } catch (e) { /* none yet */ }
    if (mark <= last) return;
    fs.writeFileSync(statePath, JSON.stringify({ last: mark }));
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: messageFor(used) },
    }));
  } catch (e) {
    // Never block a tool call over a warning.
  }
}

// AC-2: the header's numbers must equal the constants, and autocompact must equal settings.json.
function driftFindings(src, settingsText) {
  const found = {};
  for (const m of src.matchAll(/^\/\/\s+(WARN_TOKENS|AUTOCOMPACT_TOKENS|CRITICAL_TOKENS)\s+(\d+)/gm)) {
    found[m[1]] = Number(m[2]);
  }
  const want = { WARN_TOKENS, AUTOCOMPACT_TOKENS, CRITICAL_TOKENS };
  const out = [];
  for (const k of Object.keys(want)) {
    if (found[k] !== want[k]) out.push(`header says ${k} ${found[k]}, code says ${want[k]}`);
  }
  const win = JSON.parse(settingsText).autoCompactWindow;
  if (win !== AUTOCOMPACT_TOKENS) out.push(`settings.json autoCompactWindow ${win}, code says ${AUTOCOMPACT_TOKENS}`);
  return out;
}

function selfTest() {
  const { spawnSync } = require('child_process');
  const assert = require('assert');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'context-monitor-test-'));
  const userLine = JSON.stringify({ type: 'user', message: { content: 'hi' } });
  const asst = (n, extra) => JSON.stringify(Object.assign({
    type: 'assistant',
    message: { usage: { input_tokens: 2, cache_creation_input_tokens: 1000, cache_read_input_tokens: n - 1002 } },
  }, extra));
  let seq = 0;
  const run = (lines, opts = {}) => {
    const t = path.join(dir, `t${seq++}.jsonl`);
    fs.writeFileSync(t, lines.join('\n') + (opts.noNewline ? '' : '\n'));
    const env = Object.assign({}, process.env, { TMPDIR: dir });
    delete env.WF_RUN;
    Object.assign(env, opts.env || {});
    const r = spawnSync(process.execPath, [__filename], {
      input: JSON.stringify({ session_id: opts.session || `s${seq}`, transcript_path: t }), env, encoding: 'utf8',
    });
    assert.strictEqual(r.status, 0, r.stderr);
    return r.stdout ? JSON.parse(r.stdout).hookSpecificOutput.additionalContext : '';
  };
  const warn = (k) => `Context: ${k}k tokens used. Rule (\`~/.claude/CLAUDE.md\` Context): finish the current step, then \`/rollover\` mid feature or \`/save-and-clear\` at a boundary.`;
  const crit = (k) => `Context: ${k}k tokens used; autocompact (lossy) runs at 700k. Do not start new work: finish this step and \`/rollover\` now.`;

  assert.strictEqual(run([userLine, asst(149999)]), '');
  assert.strictEqual(run([userLine, asst(150000)]), warn(150));
  assert.strictEqual(run([asst(249999)]), warn(249));
  assert.strictEqual(run([asst(250000)]), warn(250));
  assert.strictEqual(run([asst(649999)]), warn(649));
  assert.strictEqual(run([asst(650000)]), crit(650));

  // One session: each level once, then the next 100k, then CRITICAL once.
  const s = { session: 'seq' };
  assert.strictEqual(run([asst(150000)], s), warn(150));
  assert.strictEqual(run([asst(249999)], s), '');
  assert.strictEqual(run([asst(250000)], s), warn(250));
  assert.strictEqual(run([asst(260000)], s), '');
  assert.strictEqual(run([asst(650000)], s), crit(650));
  assert.strictEqual(run([asst(690000)], s), '');

  // A newer sidechain line is ignored either way.
  assert.strictEqual(run([asst(100000), asst(200000, { isSidechain: true })]), '');
  assert.strictEqual(run([asst(200000), asst(100000, { isSidechain: true })]), warn(200));
  // A truncated last line falls back to the line before it.
  assert.strictEqual(run([asst(200000), asst(300000).slice(0, 60)], { noNewline: true }), warn(200));
  assert.strictEqual(run([userLine, userLine]), '');
  // Only the last 256 KB is read.
  assert.strictEqual(run([asst(200000), ...Array(3000).fill(userLine.replace('hi', 'x'.repeat(100)))]), '');
  assert.strictEqual(run([asst(650000)], { env: { WF_RUN: '1' } }), '');
  assert.strictEqual(run([asst(650000)], { session: '../escape' }), '');

  const src = fs.readFileSync(__filename, 'utf8');
  const settings = fs.readFileSync(path.join(__dirname, '..', 'settings.json'), 'utf8');
  assert.deepStrictEqual(driftFindings(src, settings), []);
  assert.strictEqual(driftFindings(src.replace(/(\/\/\s+WARN_TOKENS\s+)150000/, '$1140000'), settings).length, 1);
  assert.strictEqual(driftFindings(src.replace(/(\/\/\s+CRITICAL_TOKENS\s+)650000/, '$1600000'), settings).length, 1);
  assert.strictEqual(driftFindings(src, settings.replace(/"autoCompactWindow":\s*700000/, '"autoCompactWindow": 800000')).length, 1);

  fs.rmSync(dir, { recursive: true, force: true });
  console.log('context-monitor: all checks passed');
}

if (process.argv[2] === '--test') {
  selfTest();
} else {
  let input = '';
  // If stdin never closes, exit quietly instead of being killed as a hook error (gsd #775).
  const stdinTimeout = setTimeout(() => process.exit(0), 10000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => { clearTimeout(stdinTimeout); main(input); });
}
