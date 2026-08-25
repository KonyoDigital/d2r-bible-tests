import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/* v1628 — SOURCE-LEVEL PREVENTION GUARD for the quality palette.
   This spec renders nothing. It reads bible.html and tv/control_ui.html as TEXT.

   ROOT CAUSE IT PREVENTS: two quality colours were wrong for months because they were
   TYPED FROM MEMORY instead of read from a token. v1622 shipped --rar-unique as #f0c060
   (the console's own chrome gold). bible.html carried a whole SECOND palette (:root
   --d2-unique/--d2-set/--d2-magic) with a wrong set and magic, and a JS map _Q_HEX with
   four wrong entries. Every one of those is a literal hex sitting outside the one place
   the palette is allowed to be spelled: the :root token definition.

   The settled palette was extracted in v1627 from Konyo's own install
   (data/global/ui/layouts/_profilehd.json). It is NOT re-derived here — the values below
   are the contract, and the guard's job is to keep them the ONLY spelling of themselves.

   Two directions are checked, because they catch different halves of the defect:
     A. the settled hexes must not appear as new literals outside the token blocks
        (stops fresh hardcoding, which is how a copy goes stale later);
     B. a quality NAME followed by a hex must carry the SETTLED hex
        (stops the actual v1622/_Q_HEX defect: a second palette with WRONG values,
         which direction A can never see because a wrong hex is not the settled hex).

   COMMENT SAFETY: a comment describing a colour is textually identical to the colour
   itself. This repo has eaten real code with an over-eager stripper before, so the
   stripper here is deliberately conservative (line comments only when the TRIMMED LINE
   STARTS with //, because an inline // is indistinguishable from a URL), and its own
   correctness is asserted in a dedicated test below — both that it removes prose hexes
   and that it leaves real code standing. */

const ROOT = path.join(__dirname, '..');
const BIBLE = path.join(ROOT, 'bible.html');
const CONSOLE_UI = path.join(ROOT, 'tv', 'control_ui.html');

/* The settled palette (v1627, _profilehd.json). Keyed by quality concept. */
const SETTLED: Record<string, string> = {
  unique: '#c7b377',   // FontColorGoldYellow
  set: '#00fc00',      // FontColorGreen
  rare: '#ffff64',     // FontColorYellow
  magic: '#6e6eff',    // FontColorBlue
  crafted: '#ffa800',  // FontColorOrange
};

/* The ONLY token names allowed to spell a settled hex. `--q-orange` and `--rar-orange`
   are the crafted-quality tokens under their historical names. A `:root` definition of
   ANY OTHER token name to a settled value is a second palette — exactly the --d2-unique
   defect — and is reported, not allowed. */
const CANONICAL_TOKENS: Record<string, string> = {
  '--q-unique': 'unique', '--rar-unique': 'unique',
  '--q-set': 'set', '--rar-set': 'set',
  '--q-rare': 'rare', '--rar-rare': 'rare',
  '--q-magic': 'magic', '--rar-magic': 'magic',
  '--q-orange': 'crafted', '--rar-orange': 'crafted',
  '--rar-runeword': 'unique',  // a completed runeword's NAME is gold, same as a unique
};

/* ALLOWLIST — keyed by a STABLE SNIPPET of surrounding source text, never by line number
   (line numbers drift on every version). Each entry carries its reason. A snippet is
   matched against the ~120 characters around the hex; a NEW literal hex matches nothing
   here and therefore fails. */
type Allow = { file: 'bible' | 'console'; snippet: string; why: string };
const ALLOWLIST: Allow[] = [
  {
    file: 'console',
    snippet: '--rar-runeword',
    why: "token definition: a runeword's NAME is gold, same as a unique — deliberate alias, not a copy",
  },
];

/* ── comment stripping ─────────────────────────────────────────────────────────────── */

// Blank out comments, preserving byte offsets and newlines so line numbers reported by
// this guard still match the file.
//
// LANGUAGE-AWARE ON PURPOSE. Both targets are HTML documents, and `/*` is a comment ONLY
// inside <style> and <script>. A first cut of this stripper treated `/*` as a comment
// everywhere and swallowed live markup (bible.html's rune-stash card at ~4989 and the
// Task-Force legend chips at ~8348 both vanished into a bogus "comment" opened by a `/*`
// in ordinary body text) — the exact "stripper ate real code" failure this repo has paid
// for before. Scoping by region kills that whole class.
let LAST_MAX_SPAN = 0;
function stripComments(src: string): string {
  let maxSpan = 0;
  const n = src.length;
  const out = src.split('');
  const blank = (a: number, b: number) => {
    for (let k = a; k < b && k < n; k++) if (out[k] !== '\n') out[k] = ' ';
  };

  // Region map: which byte offsets are inside <style>/<script>.
  //
  // ⚠ SCANNED IN SOURCE ORDER, NOT PATTERN-MATCHED, AND THIS IS THE SECOND TIME THIS MAP HAS
  // BEEN THE BUG RATHER THAN THE FILE. A global /<(style|script)\b[^>]*>[\s\S]*?<\/\1>/ has no
  // idea what a comment is, so a <style> WRITTEN IN PROSE opens a region. v2094 added a doctrine
  // comment to bible.html whose text reads "The Forge pane is a <style> block and an EMPTY
  // #forge-body" (bible.html:8833) — inside an HTML comment. MEASURED: that phantom region ran
  // from line 8833 to the next real </style> at 29124, twenty thousand two hundred and ninety-one
  // lines, marking every one of them isCode=1 and isScript=0. Two whole classes of comment then
  // survived stripping inside it: <!-- --> (skipped because isCode was set) and // line comments
  // (skipped because isScript was not). The guard reported bible.html:15866 — a `//` sentence
  // reading "render in the in-game ORANGE — the same #ffa800 the crafted bucket uses" — as a
  // hardcoded palette literal, and test C's prose case for that exact line went red beside it.
  // Correct code, red guard, and the fault was the guard's own reach. [[source-reading-guard]]
  //
  // The scanner below is only ever positioned OUTSIDE a region, so at every step `<!--` really is
  // an HTML comment and may be skipped whole — which is what makes a <style> named in prose
  // invisible to it. Measured after the change: bible offenders 1 → 0, console unchanged at 0,
  // test B checked 9 → 9 in both files, largest comment span 3492 chars in both directions.
  // THE COUNT IS THE TELL: comment-blanked bytes rose 10.0% → 13.2% in bible.html (the prose the
  // phantom region had been shielding) and did not move at all in control_ui.html.
  const isCode = new Uint8Array(n);
  const isScript = new Uint8Array(n);
  const openRe = /<(style|script)\b[^>]*>/iy;
  {
    let i = 0;
    while (i < n) {
      if (src.startsWith('<!--', i)) {
        const e = src.indexOf('-->', i + 4);
        i = e < 0 ? n : e + 3;
        continue;
      }
      if (src.charCodeAt(i) === 60 /* '<' */) {
        openRe.lastIndex = i;
        const t = openRe.exec(src);
        if (t) {
          const tag = t[1].toLowerCase();
          const bodyStart = i + t[0].length;
          // an unclosed region runs to EOF — the same reading the old regex gave by dropping it
          const closeRe = new RegExp('</' + tag + '\\s*>', 'gi');
          closeRe.lastIndex = bodyStart;
          const c = closeRe.exec(src);
          const bodyEnd = c ? c.index : n;
          for (let k = bodyStart; k < bodyEnd; k++) {
            isCode[k] = 1;
            if (tag === 'script') isScript[k] = 1;
          }
          i = c ? c.index + c[0].length : n;
          continue;
        }
      }
      i++;
    }
  }

  let i = 0;
  while (i < n) {
    // <!-- --> is an HTML comment only OUTSIDE <style>/<script>.
    if (!isCode[i] && src.startsWith('<!--', i)) {
      const e = src.indexOf('-->', i + 4);
      const end = e < 0 ? n : e + 3;
      blank(i, end); i = end; continue;
    }
    // /* */ is a comment only INSIDE <style>/<script>, may not escape its region, and
    // may not be glued to a preceding word character. That last rule is not cosmetic: a
    // MIME pattern in an ordinary string — bible.html has accept="image/*" in the AI
    // Checker's file input — otherwise opens a bogus comment that ran 969 lines and ate
    // the `var Q = { unique:'#c7b377', set:'#00ff00', ... }` palette map, silently turning
    // test B GREEN over a real defect. A genuine comment is always preceded by start of
    // region, whitespace, or one of ; { } ( ) , : and never by [A-Za-z0-9._/-].
    if (isCode[i] && src.startsWith('/*', i) && !/[A-Za-z0-9._/-]/.test(src[i - 1] || ' ')) {
      const e = src.indexOf('*/', i + 2);
      let end = e < 0 ? n : e + 2;
      for (let k = i; k < end; k++) if (!isCode[k]) { end = k; break; }
      if (end - i > maxSpan) maxSpan = end - i;
      blank(i, end); i = end; continue;
    }
    i++;
  }

  // Line comments LAST, CONSERVATIVELY, and only inside <script>: only when the trimmed
  // line starts with //. An inline // cannot be told apart from a URL ("https://")
  // without a full JS parser, and under-stripping only costs one extra reported site —
  // over-stripping eats code.
  LAST_MAX_SPAN = maxSpan;
  const text = out.join('');
  let off = 0;
  return text.split('\n').map((ln) => {
    const start = off; off += ln.length + 1;
    return (isScript[start] && ln.trimStart().startsWith('//')) ? ' '.repeat(ln.length) : ln;
  }).join('\n');
}

function lineOf(src: string, index: number): number {
  let line = 1;
  for (let k = 0; k < index; k++) if (src.charCodeAt(k) === 10) line++;
  return line;
}

function read(which: 'bible' | 'console'): { raw: string; code: string; maxSpan: number } {
  const raw = fs.readFileSync(which === 'bible' ? BIBLE : CONSOLE_UI, 'utf8');
  const code = stripComments(raw);
  return { raw, code, maxSpan: LAST_MAX_SPAN };
}

type Site = { file: string; line: number; hex: string; context: string };

function findSettledLiterals(which: 'bible' | 'console'): { offenders: Site[]; okTokenDefs: number; okAllowed: number } {
  const { raw, code } = read(which);
  const offenders: Site[] = [];
  let okTokenDefs = 0;
  let okAllowed = 0;
  const hexes = Object.values(SETTLED);
  const re = new RegExp(hexes.join('|'), 'gi');
  let m: RegExpExecArray | null;
  while ((m = re.exec(code)) !== null) {
    const hex = m[0].toLowerCase();
    const before = code.slice(Math.max(0, m.index - 60), m.index);
    const around = code.slice(Math.max(0, m.index - 60), m.index + 60);

    // (1) a canonical :root token definition — `--q-unique:#c7b377`
    const def = /(--[a-z0-9-]+)\s*:\s*$/i.exec(before);
    if (def) {
      const tok = def[1].toLowerCase();
      const concept = CANONICAL_TOKENS[tok];
      if (concept && SETTLED[concept].toLowerCase() === hex) { okTokenDefs++; continue; }
      // A non-canonical token spelled with a settled value. If the token NAME carries a
      // quality word it is a SECOND PALETTE (the --d2-unique defect); otherwise it is a
      // one-off tint variable that still hardcodes the palette (e.g. an inline --tc).
      const secondPalette = /-(unique|set|magic|rare|orange|crafted|runeword)$/i.test(tok);
      offenders.push({
        file: which, line: lineOf(code, m.index), hex,
        context: secondPalette ? `SECOND PALETTE: ${tok}: ${hex}` : `hardcoded tint var: ${tok}: ${hex}`,
      });
      continue;
    }

    // (2) documented exception
    const allowed = ALLOWLIST.find((a) => a.file === which && around.includes(a.snippet));
    if (allowed) { okAllowed++; continue; }

    offenders.push({ file: which, line: lineOf(code, m.index), hex, context: raw.split('\n')[lineOf(code, m.index) - 1].trim().slice(0, 110) });
  }
  return { offenders, okTokenDefs, okAllowed };
}

/* ── A. no literal settled hex outside the token blocks ────────────────────────────── */

for (const which of ['bible', 'console'] as const) {
  test(`v1628 A/${which}: settled quality hexes appear only in canonical token definitions`, () => {
    const { offenders, okTokenDefs, okAllowed } = findSettledLiterals(which);
    // Non-vacuity: the guard must actually have found the token block it is protecting.
    expect(okTokenDefs, `${which}: no canonical token definition found — the guard is looking at the wrong file`).toBeGreaterThan(0);
    const report = offenders.map((o) => `  ${o.file} line ${o.line}  ${o.hex}  ${o.context}`).join('\n');
    expect(offenders.length, `literal quality hexes outside the token block (${offenders.length}); use var(--q-*)/var(--rar-*):\n${report}\n(allowlisted: ${okAllowed}, token defs: ${okTokenDefs})`).toBe(0);
  });
}

/* ── B. a quality NAME followed by a hex must carry the SETTLED hex ────────────────── */

for (const which of ['bible', 'console'] as const) {
  test(`v1628 B/${which}: every quality-keyed colour equals its settled token value`, () => {
    const { raw, code } = read(which);
    const bad: string[] = [];
    let checked = 0;

    // B1 — JS/object map form:  unique:'#c7b377'   set: "#00fc00"   magic:#6e6eff
    const mapRe = /\b(unique|set|magic|rare|crafted)\s*:\s*['"]?(#[0-9a-fA-F]{6})/g;
    let m: RegExpExecArray | null;
    while ((m = mapRe.exec(code)) !== null) {
      checked++;
      const want = SETTLED[m[1].toLowerCase()];
      if (m[2].toLowerCase() !== want) {
        bad.push(`${which} line ${lineOf(code, m.index)}: ${m[1]} = ${m[2]} — settled is ${want}  |  ${raw.split('\n')[lineOf(code, m.index) - 1].trim().slice(0, 110)}`);
      }
    }

    // B2 — CSS custom-property form, incl. second palettes:  --d2-set:#2fe35e
    const cssRe = /--(?:q|rar|d2)-(unique|set|magic|rare|orange|crafted)\s*:\s*(#[0-9a-fA-F]{6})/g;
    while ((m = cssRe.exec(code)) !== null) {
      checked++;
      const concept = m[1].toLowerCase() === 'orange' ? 'crafted' : m[1].toLowerCase();
      const want = SETTLED[concept];
      if (m[2].toLowerCase() !== want) {
        bad.push(`${which} line ${lineOf(code, m.index)}: --*-${m[1]} = ${m[2]} — settled is ${want}`);
      }
    }

    // B3 — var() fallback form:  var(--q-unique,#c7b377) — the fallback must not drift
    //      from the token it is standing in for.
    const varRe = /var\(\s*(--(?:q|rar)-[a-z]+)\s*,\s*(#[0-9a-fA-F]{6})/g;
    while ((m = varRe.exec(code)) !== null) {
      const concept = CANONICAL_TOKENS[m[1].toLowerCase()];
      if (!concept) continue;
      checked++;
      if (m[2].toLowerCase() !== SETTLED[concept]) {
        bad.push(`${which} line ${lineOf(code, m.index)}: var(${m[1]}) fallback ${m[2]} drifted — token is ${SETTLED[concept]}`);
      }
    }

    // Non-vacuity: a pass here must mean "N quality-keyed colours were inspected and all
    // matched", never "the regexes matched nothing".
    expect(checked, `${which}: found ZERO quality-keyed colours to check — the matcher is broken, not the file`).toBeGreaterThan(0);
    expect(bad.length, `quality colours that disagree with the settled palette (${bad.length} of ${checked} checked):\n${bad.join('\n')}`).toBe(0);
  });
}

/* ── C. the comment stripper is correct in BOTH directions ─────────────────────────── */

test('v1628 C: comment stripper removes prose hexes and leaves real code standing', () => {
  // Prose that QUOTES a hex — must not trip the guard. Keyed by stable snippets, never
  // line numbers. These are CANDIDATES, not a fixed list: bible.html's doctrine comments
  // get rewritten (one of these snippets was edited out mid-audit), so the contract is
  // "at least MIN of these must still exist, and every one that exists must be stripped",
  // backed by a dynamic floor below that no amount of snippet rot can make vacuous.
  const proseSnippets: { file: 'bible' | 'console'; snippet: string }[] = [
    { file: 'bible', snippet: 'reads as gold on the dark bg instead of washing out' },
    { file: 'bible', snippet: 'the bar renders style="color:' },
    { file: 'bible', snippet: 'render in the in-game ORANGE' },
    { file: 'bible', snippet: 'quality palette — unique gold' },
    { file: 'console', snippet: 'FOR FORGE:' },
    { file: 'console', snippet: "unique is D2's" },
  ];
  const MIN_CASES: Record<string, number> = { bible: 2, console: 2 };
  const hexRe = /#(?:c7b377|00fc00|ffff64|6e6eff|ffa800|ff7d3c|00ff00|6969ff)/i;
  const seen: Record<string, number> = { bible: 0, console: 0 };

  for (const p of proseSnippets) {
    const { raw, code } = read(p.file);
    const rawLines = raw.split('\n');
    const idx = rawLines.findIndex((l) => l.includes(p.snippet));
    if (idx < 0) continue;               // snippet rotted away; the floor below covers us
    if (!hexRe.test(rawLines[idx])) continue;
    seen[p.file]++;
    // Non-vacuity per case: the RAW line really does quote a hex, and after stripping the
    // whole line is gone — so prose can never be mistaken for a colour declaration.
    expect(rawLines[idx], `${p.file}:${idx + 1} was expected to quote a hex in prose`).toMatch(hexRe);
    expect(code.split('\n')[idx].trim(), `${p.file}:${idx + 1} comment survived stripping — the guard would flag prose`).toBe('');
  }
  for (const f of ['bible', 'console'] as const) {
    expect(seen[f], `only ${seen[f]} prose-hex cases still resolve in ${f} — add a fresh snippet, do not lower MIN_CASES`).toBeGreaterThanOrEqual(MIN_CASES[f]);
  }

  // Dynamic floor: independently of the snippet list, each file must contain several
  // lines that quote a settled hex AND are fully neutralised by the stripper. If this
  // ever drops to zero the comment-safety proof has become vacuous.
  for (const f of ['bible', 'console'] as const) {
    const { raw, code } = read(f);
    const rl = raw.split('\n'), cl = code.split('\n');
    let neutralised = 0;
    for (let i = 0; i < rl.length; i++) {
      if (hexRe.test(rl[i]) && rl[i].trim() !== '' && cl[i].trim() === '') neutralised++;
    }
    expect(neutralised, `${f}: no comment line quoting a palette hex was neutralised — comment safety is untested`).toBeGreaterThanOrEqual(2);
  }

  // The other direction — the stripper must NOT eat real code.
  const survivors: { file: 'bible' | 'console'; snippet: string }[] = [
    { file: 'bible', snippet: '--q-unique:#c7b377' },        // the :root token block itself
    { file: 'bible', snippet: 'var _Q_HEX' },                 // real JS on a line that quotes hexes
    { file: 'console', snippet: '--rar-unique:' },
  ];
  for (const s of survivors) {
    const { code } = read(s.file);
    expect(code.includes(s.snippet), `stripper ate real code in ${s.file}: "${s.snippet}" no longer present`).toBe(true);
  }

  // Blast-radius bound. An unterminated /* inside a JS string would blank the rest of a
  // region, so the sharp signal is the LARGEST SINGLE comment span, not the aggregate:
  // both files are doctrine-heavy (control_ui.html measures 15.3% of its bytes in block
  // comments across many small headers, largest span 2765 chars) so an aggregate bound
  // tight enough to be meaningful would just be flaky. A single span over 4000 chars is
  // a runaway, and the survivor assertions above are the real proof code was not eaten.
  for (const f of ['bible', 'console'] as const) {
    const { raw, code, maxSpan } = read(f);
    expect(maxSpan, `${f}: a single block-comment span of ${maxSpan} chars — runaway /* opened inside a string`).toBeLessThan(4000);
    const eaten = 1 - code.replace(/\s/g, '').length / raw.replace(/\s/g, '').length;
    expect(eaten, `${f}: stripper removed ${(eaten * 100).toFixed(1)}% of non-whitespace`).toBeLessThan(0.4);
  }
});

/* ── D. the DO-NOT-TOUCH boundary: different concepts must survive ─────────────────── */

test('v1628 D: craft-gem colours and the rune-item colour are NOT quality tokens and survive', () => {
  const { raw } = read('bible');
  // These name a GEM a craft needs, not an item quality. A future "tokenize every hex"
  // sweep that folds them into the quality palette must go red here.
  const different: { hex: string; concept: string }[] = [
    { hex: '#b48ce0', concept: 'craft gem — Caster' },
    { hex: '#e0556a', concept: 'craft gem — Blood' },
    { hex: '#5fd07a', concept: 'craft gem — Safety' },
    { hex: '#5b8ff0', concept: 'craft gem — Hit Power' },
    { hex: '#ff7d3c', concept: '--rune — the colour of a RUNE ITEM (El, Eld), not a runeword name' },
  ];
  for (const d of different) {
    expect(new RegExp(d.hex, 'i').test(raw), `${d.hex} (${d.concept}) vanished from bible.html — it is a DIFFERENT CONCEPT from the quality palette and must not be tokenized away`).toBe(true);
  }
  // --rune must still be its own token, not aliased to a quality colour.
  expect(raw).toMatch(/--rune:\s*#ff7d3c/i);

  // And the settled palette must still exist as tokens in both files (so D cannot pass
  // by the palette having been deleted).
  const bibleRoot = raw.split('\n')[11] || '';
  for (const [concept, hex] of Object.entries(SETTLED)) {
    const tok = concept === 'crafted' ? '--q-orange' : `--q-${concept}`;
    expect(bibleRoot.toLowerCase(), `bible :root lost ${tok}`).toContain(`${tok}:${hex}`);
  }
  const con = read('console').raw.toLowerCase();
  for (const [concept, hex] of Object.entries(SETTLED)) {
    const tok = concept === 'crafted' ? '--rar-orange' : `--rar-${concept}`;
    expect(new RegExp(`${tok}\\s*:\\s*${hex}`).test(con), `console :root lost ${tok}: ${hex}`).toBe(true);
  }
});
