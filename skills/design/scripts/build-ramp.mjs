#!/usr/bin/env node
// build-ramp.mjs - one brand hue in, a full contrast-verified OKLCH token set out.
// Requires: npm i culori   (verified against culori 4.x, node 24)
//
// Usage:
//   node build-ramp.mjs --hue 152 --sat 0.92 --tune 0.18
//   node build-ramp.mjs --hue 152 --json
//
// Design: 12 steps with Radix step semantics. Steps 1-10 sit on a fixed
// perceptual lightness ladder. Steps 9, 11, 12 are SOLVED for a contrast
// target instead of being placed by eye - that is the contrast-by-construction
// part. Chroma is a fraction of the maximum in-gamut chroma AT THAT LIGHTNESS,
// which produces the arc automatically and never clips.

import { inGamut, wcagContrast, formatCss, converter } from 'culori';

// Solve margin. Ramps are computed in float OKLCH and shipped as rounded hex;
// solving for exactly the target let quantisation land just under it in the emitted file.
const QUANT = 0.08;

// The step-11 text is SOLVED against step 2 (solveL(mk11, bg2, ...) below), so the
// stylesheet MUST pair it with step 2. These two constants are the single source for
// both sides: the previous version solved against 2 and emitted on 3, so --check
// reported 384/384 while every semantic text-on-bg pair shipped near 4.0:1, below AA.
const SEMANTIC_TEXT_STEP = 11;
const SEMANTIC_BG_STEP = 2;

const inSrgb = inGamut('rgb');
const toRgb = converter('rgb');

// ---------------------------------------------------------------- args
const argv = process.argv.slice(2);
const arg = (k, d) => {
  const i = argv.indexOf('--' + k);
  return i === -1 ? d : argv[i + 1];
};
const flag = (k) => argv.includes('--' + k);

const BRAND_HUE = Number(arg('hue', 152));
const SAT = Number(arg('sat', 0.9));       // fraction of max in-gamut chroma at step 9
const TUNE = Number(arg('tune', 0.18));    // how far semantic hues bend toward the brand
const HUE_SHIFT = Number(arg('shift', -6)); // deg of hue drift from step 1 to step 12
const NEUTRAL_C = Number(arg('neutralc', 0.008));
const ON_ACTION = arg('onaction', 'auto'); // auto | white | ink

// ---------------------------------------------------------------- primitives
const ok = (l, c, h) => ({ mode: 'oklch', l, c, h });

// Largest chroma that stays inside sRGB for this L and H. Binary search: the
// in-gamut set is an interval [0, cmax] for fixed L,H, so this converges.
function maxChroma(l, h) {
  let lo = 0, hi = 0.42;
  for (let i = 0; i < 26; i++) {
    const mid = (lo + hi) / 2;
    if (inSrgb(ok(l, mid, h))) lo = mid; else hi = mid;
  }
  return lo;
}

// Relative-chroma constructor. satFrac is a FRACTION of what the gamut allows
// here, so the absolute chroma arc (low at the pale and deep ends, peak in the
// mid-tones) falls out of the gamut shape instead of being hand-tuned.
const mk = (l, h, satFrac) => ok(l, satFrac * maxChroma(l, h), h);

const cr = (a, b) => wcagContrast(a, b);

// Scan L from `from` toward `to`, return the first colour meeting `target`
// contrast against `bg`. Scanning (not bisecting) because relative luminance
// is only near-monotonic in L once chroma tracks the gamut boundary.
// `make` is the FINAL colour factory for the step (chroma included), so what
// gets verified is exactly what gets emitted. Solving at one chroma and
// shipping another is how a "guaranteed" ramp quietly stops being one.
function solveL(make, bg, target, from, to, steps = 900) {
  let best = null;
  for (let i = 0; i <= steps; i++) {
    const l = from + (to - from) * (i / steps);
    const col = make(l);
    const c = cr(col, bg);
    if (!best || c > best.ratio) best = { l, col, ratio: c };
    if (c >= target) return { l, col, ratio: c, ok: true };
  }
  return { ...best, ok: false };
}

// ---------------------------------------------------------------- the ladder
// Fixed perceptual lightness ladder, light theme. Steps 1-2 page/subtle,
// 3-5 component fills, 6-8 borders, 9-10 solid fills, 11-12 text.
// 9, 11, 12 are placeholders: they get solved below.
const LADDER_LIGHT = [0.993, 0.977, 0.955, 0.932, 0.906, 0.872, 0.826, 0.755, null, null, null, null];
const LADDER_DARK  = [0.178, 0.213, 0.257, 0.291, 0.325, 0.372, 0.437, 0.531, null, null, null, null];

// Relative chroma per step. Constant would also arc, but tapering the ends
// keeps step 1-2 from reading tinted and keeps text steps from vibrating.
const SAT_CURVE = [0.10, 0.16, 0.26, 0.34, 0.42, 0.50, 0.60, 0.72, 1.00, 0.96, 0.78, 0.56];

const hueAt = (h, i) => h + HUE_SHIFT * (i / 11);

function buildScale({ hue, sat, dark = false, neutral = false }) {
  const ladder = dark ? LADDER_DARK : LADDER_LIGHT;
  // Dark UIs need less chroma at the same perceived intensity: on a dark
  // ground a saturated fill sits at a much larger colour-difference from its
  // background than the same fill on white, so it reads as glare.
  const chromaScale = dark ? 0.78 : 1;

  const steps = new Array(12).fill(null);
  const satOf = (i) => neutral ? null : sat * SAT_CURVE[i] * chromaScale;

  // Pass 1: the placed steps (1-8).
  for (let i = 0; i < 8; i++) {
    const h = hueAt(hue, i);
    steps[i] = neutral
      ? ok(ladder[i], NEUTRAL_C * (dark ? 1.25 : 1), h)
      : mk(ladder[i], h, satOf(i));
  }

  const bg2 = steps[1]; // step 2 is the contrast reference, per Radix
  const bg1 = steps[0];

  // Pass 2: step 9, the solid fill / action colour. Solved so that ONE of
  // white or the scale's own step-12 ink clears 4.5:1 ON the fill, and the
  // fill itself clears 3:1 against step 1 (WCAG 1.4.11 non-text).
  const h9 = hueAt(hue, 8);
  const s9 = neutral ? null : sat * SAT_CURVE[8] * chromaScale;
  const mk9 = (l) => neutral ? ok(l, NEUTRAL_C * 2.5, h9) : mk(l, h9, s9);

  let step9 = null, onAction = null;
  const white = ok(1, 0, h9);
  const ink = ok(dark ? 0.16 : 0.18, neutral ? 0 : 0.03, h9);
  // Sweep the whole plausible solid-fill band, keep every L where BOTH
  // directions pass (label ON the fill >= 4.5:1, fill ON the page >= 3:1),
  // then pick the one with the MOST chroma. That is the definition of a
  // Radix-style step 9: the purest step in the scale that is still usable.
  const band = [0.86, 0.36];
  let bestC = -1;
  for (let i = 0; i <= 500; i++) {
    const l = band[0] + (band[1] - band[0]) * (i / 500);
    const cand = mk9(l);
    const vsWhite = cr(cand, white);
    const vsInk = cr(cand, ink);
    const vsPage = cr(cand, bg1);
    const fg = ON_ACTION === 'white' ? { c: white, r: vsWhite, n: 'white' }
             : ON_ACTION === 'ink'   ? { c: ink, r: vsInk, n: 'ink' }
             : vsWhite >= vsInk      ? { c: white, r: vsWhite, n: 'white' }
                                     : { c: ink, r: vsInk, n: 'ink' };
    if (fg.r >= 4.5 + QUANT && vsPage >= 3 + QUANT && cand.c > bestC) {
      bestC = cand.c; step9 = cand; onAction = fg;
    }
  }
  if (!step9) { // no L satisfies both: keep the label pass, report the miss
    const r = solveL(mk9, white, 4.5 + QUANT, band[0], band[1]);
    step9 = r.col; onAction = { c: white, r: r.ratio, n: 'white(FORCED)' };
  }
  steps[8] = step9;

  // Step 10 = hovered solid: one perceptual notch further from the page.
  steps[9] = neutral
    ? ok(step9.l + (dark ? 0.05 : -0.045), step9.c, hueAt(hue, 9))
    : mk(step9.l + (dark ? 0.05 : -0.045), hueAt(hue, 9), sat * SAT_CURVE[9] * chromaScale);

  // Pass 3: text steps, solved against step 2 for exact WCAG targets.
  const mk11 = (l) => neutral
    ? ok(l, NEUTRAL_C * 1.5, hueAt(hue, 10))
    : mk(l, hueAt(hue, 10), sat * SAT_CURVE[10] * chromaScale);
  const mk12 = (l) => neutral
    ? ok(l, NEUTRAL_C * 1.2, hueAt(hue, 11))
    : mk(l, hueAt(hue, 11), sat * SAT_CURVE[11] * chromaScale);
  const t11 = solveL(mk11, bg2, 4.5 + QUANT, dark ? 0.58 : 0.64, dark ? 0.98 : 0.26);
  const t12 = solveL(mk12, bg2, 7.0, dark ? 0.70 : 0.50, dark ? 1.0 : 0.12);
  steps[10] = t11.col;
  steps[11] = t12.col;
  const v11 = cr(steps[10], bg2), v12 = cr(steps[11], bg2);

  return {
    steps,
    report: {
      'step9 vs step1 (non-text 3:1)': cr(steps[8], bg1),
      [`on-action = ${onAction.n} (4.5:1)`]: onAction.r,
      'step11 vs step2 (4.5:1)': v11,
      'step12 vs step2 (7:1)': v12,
      'step12 vs step1': cr(steps[11], bg1),
    },
    onAction: onAction.c,
  };
}

// ---------------------------------------------------------------- semantics
// Semantic hues bend TOWARD the brand hue by `tune`, so success/danger belong
// to this brand instead of being bootstrap green and bootstrap red.
const shortest = (from, to) => ((to - from + 540) % 360) - 180;
const bend = (anchor, brand, t) => (anchor + shortest(anchor, brand) * t + 360) % 360;

const ANCHORS = { danger: 27, warning: 75, success: 150, info: 240 };

function semanticHues(brand, tune) {
  const out = {};
  for (const [k, a] of Object.entries(ANCHORS)) out[k] = bend(a, brand, tune);
  return out;
}

// ---------------------------------------------------------------- emit
const fmt = (c) => {
  const o = { mode: 'oklch', l: +c.l.toFixed(4), c: +c.c.toFixed(4), h: +(((c.h % 360) + 360) % 360).toFixed(2) };
  return formatCss(o);
};
const hex = (c) => {
  const r = toRgb(c);
  const p = (v) => Math.round(Math.min(1, Math.max(0, v)) * 255).toString(16).padStart(2, '0');
  return '#' + p(r.r) + p(r.g) + p(r.b);
};

function main() {
  const sem = semanticHues(BRAND_HUE, TUNE);
  const scales = {};
  const reports = {};

  const defs = [
    ['brand', BRAND_HUE, SAT, false],
    ['neutral', BRAND_HUE, SAT, true],
    ...Object.entries(sem).map(([k, h]) => [k, h, SAT * 0.95, false]),
  ];

  for (const theme of ['light', 'dark']) {
    scales[theme] = {};
    reports[theme] = {};
    for (const [name, hue, sat, neutral] of defs) {
      const r = buildScale({ hue, sat, dark: theme === 'dark', neutral });
      scales[theme][name] = r.steps;
      reports[theme][name] = r.report;
      if (name === 'brand') scales[theme].__onAction = r.onAction;
    }
  }

  // collision guard: a semantic hue too close to the brand hue stops being a signal
  const warns = [];
  for (const [k, h] of Object.entries(sem)) {
    const d = Math.abs(shortest(BRAND_HUE, h));
    if (d < 25) warns.push(`WARN: ${k} hue ${h.toFixed(0)} is ${d.toFixed(0)}deg from brand ${BRAND_HUE} - state will read as brand. Lower --tune or move the brand hue.`);
  }

  if (flag('json')) {
    console.log(JSON.stringify({ brandHue: BRAND_HUE, semanticHues: sem, scales, reports, warns }, null, 2));
    return;
  }

  const block = (theme, sel) => {
    const s = scales[theme];
    const lines = [`${sel} {`];
    for (const [name, hue, , ] of defs) {
      s[name].forEach((c, i) => lines.push(`  --${name}-${i + 1}: ${fmt(c)}; /* ${hex(c)} */`));
    }
    lines.push('');
    lines.push('  /* semantic layer - components consume ONLY these */');
    lines.push('  --color-bg-page: var(--neutral-1);');
    lines.push('  --color-bg-surface: var(--neutral-2);');
    lines.push('  --color-bg-raised: var(--neutral-3);');
    lines.push('  --color-bg-sunken: var(--neutral-2);');
    lines.push('  --color-border-subtle: var(--neutral-6);');
    lines.push('  --color-border-strong: var(--neutral-8);');
    lines.push('  --color-text-primary: var(--neutral-12);');
    lines.push('  --color-text-secondary: var(--neutral-11);');
    lines.push('  --color-text-muted: var(--neutral-11);');
    lines.push('  --color-action: var(--brand-9);');
    lines.push('  --color-action-hover: var(--brand-10);');
    lines.push('  --color-action-active: var(--brand-10);');
    lines.push(`  --color-text-on-action: ${fmt(s.__onAction)};`);
    lines.push('  --color-focus-ring: var(--brand-8);');
    for (const k of Object.keys(ANCHORS)) {
      lines.push(`  --color-${k}: var(--${k}-9);`);
      lines.push(`  --color-${k}-bg: var(--${k}-${SEMANTIC_BG_STEP});`);
      lines.push(`  --color-${k}-text: var(--${k}-${SEMANTIC_TEXT_STEP});`);
    }
    lines.push('}');
    return lines.join('\n');
  };

  console.log(`/* Generated from brand hue ${BRAND_HUE}deg, sat ${SAT}, semantic tune ${TUNE}.`);
  console.log(`   Semantic hues: ${Object.entries(sem).map(([k, v]) => `${k} ${v.toFixed(0)}`).join(', ')} */`);
  console.log(block('light', ':root'));
  console.log();
  console.log(block('dark', ':root[data-theme="dark"]'));
  console.log();
  console.log('/* ---- contrast verification (WCAG 2.2 ratios, computed, not eyeballed) ----');
  for (const theme of ['light', 'dark']) {
    console.log(`  [${theme}]`);
    for (const [name, rep] of Object.entries(reports[theme])) {
      const parts = Object.entries(rep).map(([k, v]) => `${k}=${v.toFixed(2)}`);
      console.log(`    ${name.padEnd(8)} ${parts.join('  ')}`);
    }
  }
  warns.forEach((w) => console.log('  ' + w));
  console.log('*/');
}


// ---------------------------------------------------------------- self check
// Runnable proof the construction holds, not a claim that it does.
// Breaks loudly if any solved pair misses its target on any hue.
function selfCheck() {
  const targets = {
    'step9 vs step1 (non-text 3:1)': 3,
    'step11 vs step2 (4.5:1)': 4.5,
    'step12 vs step2 (7:1)': 7,
  };
  let fails = 0, checks = 0;
  for (let hue = 0; hue < 360; hue += 15) {
    for (const dark of [false, true]) {
      for (const neutral of [false, true]) {
        const r = buildScale({ hue, sat: SAT, dark, neutral });
        for (const [k, v] of Object.entries(r.report)) {
          const t = targets[k] ?? (k.startsWith('on-action') ? 4.5 : null);
          if (t === null) continue;
          checks++;
          if (v + 1e-9 < t) {
            fails++;
            console.error(`FAIL hue=${hue} dark=${dark} neutral=${neutral} ${k} = ${v.toFixed(3)} < ${t}`);
          }
        }
      }
    }
  }
  console.log(`${checks - fails}/${checks} contrast targets met across 24 hues x light/dark x colour/neutral`);
  console.log(`semantic pair emitted as step ${SEMANTIC_TEXT_STEP} on step ${SEMANTIC_BG_STEP}; step ${SEMANTIC_TEXT_STEP} is solved against step ${SEMANTIC_BG_STEP} - single source, cannot diverge`);
  process.exit(fails ? 1 : 0);
}

if (flag('check')) selfCheck(); else main();
