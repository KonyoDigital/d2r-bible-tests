import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1733 — A CSS VARIABLE THAT IS REFERENCED MUST BE DEFINED, OR CARRY A FALLBACK.
//
// `--gold-dim` was referenced 192 times in bible.html and defined ZERO times. It resolved to the
// empty string, and CSS handles that silently and destructively:
//
//   * `border: 1px solid var(--gold-dim)` — the whole shorthand is invalid at computed-value time,
//     so the border becomes `none`. 160 elements were carrying a border that never drew.
//   * `color: var(--gold-dim)` — the declaration is dropped and the element inherits instead, so
//     243 elements silently took their parent's colour.
//
// Measured, not argued: defining the token changed 403 rendered elements across 11 tabs. Nothing
// errored, nothing logged, and every gate stayed green — the page just quietly rendered a design
// nobody had authored. This is the CSS instance of a plumbing joint built on both ends and never
// connected. [[plumbing-with-no-tap]]
//
// The value is not invented. `tv/control_ui.html` — the other surface of the same product — has
// defined `--gold-dim: #a07830` all along, so the fix names the existing source rather than
// picking a new colour. [[copy-drift]] The same audit found five more:
//
//   bible.html    --bg-elev0 (12), --bg-elev1 (17)  -> aliased to the file's own --surface /
//                     --surface-2 ladder, verified ORDERED (luminance 21.0 < 29.3, so the raised
//                     surface really is lighter). Aliases, not new hexes: one source per colour.
//                 --best-dim (4)   -> color-mix from --best, the idiom this file already uses 72x
//   NOT fixed, deliberately: --rar-rune looked like a sixth case and is not one. Its only
//   occurrence in bible.html sits inside a comment that documents a PAST state ("the Forge room
//   now wears --rune"). Defining it would have added a token nothing references. Stripping
//   comments before auditing is what told the difference.
//   control_ui    --text-dim (17)  -> the value bible.html defines for that exact token name
//                 --body (1)       -> a FONT FAMILY inside a `font:` shorthand, which invalidated
//                     the entire declaration and took --fw-semibold, --fs-xs and the 1.35
//                     line-height down with it. The console defines only --mono and --serif, so
//                     rather than invent a third family the shorthand became longhands: the three
//                     intended properties now apply and the family stays inherited, which is what
//                     the element was getting anyway. [[unknown-stays-unknown]]
//
// This gate is STATIC on purpose. A runtime probe over getComputedStyle cannot see tokens that are
// assigned inline on elements built later, and it reported nine bible tokens as undefined that are
// nothing of the kind — including `--q-`, which is not a token at all but the literal prefix of
// `var(--q-${quality})` in a template string. Reading the source instead removes both errors.
// [[feedback-suspect-the-instrument]]

const FILES = ['bible.html', 'tv/control_ui.html'];

function audit(file: string) {
  const raw = fs.readFileSync(path.resolve(__dirname, '..', file), 'utf8');
  /* Strip block comments FIRST. `--a` is referenced exactly once in tv/control_ui.html and that
     one occurrence is inside a comment explaining that the values are assigned inline — prose
     describing the code, not code. An audit that reads comments reports defects that do not
     exist, which is the same failure as a guard blinded BY a comment, pointed the other way.
     [[feedback-comments-vs-code]] */
  const s = raw.replace(/\/\*[\s\S]*?\*\//g, ' ');
  const bad: string[] = [];
  let referenced = 0;
  const seen = new Set<string>();
  for (const m of s.matchAll(/var\(\s*(--[a-zA-Z0-9-]+)\s*(,)?/g)) {
    const token = m[1];
    if (m[2]) continue;                       // has a fallback — cannot render as nothing
    if (seen.has(token)) continue;
    seen.add(token);
    referenced++;
    // `var(--q-${quality})` is a template string, not a token reference
    if (/^--q-$/.test(token)) continue;
    const assigned =
      new RegExp(String.raw`${token}\s*:`).test(s) ||                       // CSS rule or inline style
      new RegExp(String.raw`setProperty\(\s*['"\`]${token}`).test(s);       // set from JS
    if (!assigned) bad.push(token);
  }
  return { bad, referenced };
}

test.describe('v1733 — every CSS token resolves to something', () => {
  for (const file of FILES) {
    test(`★★★ ${file}: no bare var() names a token nothing ever defines`, async () => {
      const r = audit(file);
      // non-vacuity: this must actually have found bare var() references to judge
      expect(r.referenced, `${file}: no fallback-less var() references were found at all`)
        .toBeGreaterThan(20);
      expect(r.bad, `${file}: referenced but never defined — these render as NOTHING, silently: ` +
        r.bad.join(', ')).toEqual([]);
    });
  }


  /* v1734 — AN UNDEFINED TOKEN MAY NOT RENDER AS TWO DIFFERENT COLOURS.
     The first version of this gate demanded that every fallback EQUAL the definition it backs up.
     It was wrong, and the count said so: it flagged 28 sites, including --text-dim with twelve
     different fallbacks and --text with eight. Approximate fallbacks are this file's house style,
     not a defect — and while a token is defined the token wins, so those fallbacks are dead code
     that renders nothing. A gate demanding ~28 edits with no visual effect is a style opinion
     wearing a gate's clothes. [[feedback-suspect-the-instrument]]

     The invariant that IS real: when a token is NOT defined, its fallbacks are LIVE, and if they
     disagree the same design token renders as different colours in different places.

     Both files were red on exactly this. tv/control_ui.html referenced --gold-bright twice with no
     definition, so #itip's border drew #d4a849 while .hh-go:hover drew #f0c060 — one token, two
     colours, on screen together. And bible.html's --gold-dim was worse than "undefined": across
     its fallback sites it rendered as SIX colours at once (#6a5a38, #8a6f2e, #9a7426, #a07830,
     #c8a24a, #caa24a) on top of the 192 bare uses that rendered as nothing.

     One of those six was already #a07830 — the value tv/control_ui.html defines — which is a
     second, independent witness that the value chosen in v1733 was the right one.
     [[d2r-multiwitness-corroboration]] */
  for (const file of FILES) {
    test(`★★★ ${file}: an undefined token does not render as two different values`, async () => {
      const raw = fs.readFileSync(path.resolve(__dirname, '..', file), 'utf8');
      const s = raw.replace(/\/\*[\s\S]*?\*\//g, ' ');
      const fb = new Map<string, Set<string>>();
      for (const m of s.matchAll(/var\(\s*(--[a-zA-Z0-9-]+)\s*,\s*([^)]+?)\s*\)/g)) {
        if (!fb.has(m[1])) fb.set(m[1], new Set());
        fb.get(m[1])!.add(m[2].toLowerCase());
      }
      const bad: string[] = [];
      let checked = 0;
      for (const [token, vals] of fb) {
        // a DEFINED token always wins, so its fallbacks are dead and may drift harmlessly
        if (new RegExp(String.raw`${token}\s*:`).test(s)) continue;
        checked++;
        if (vals.size > 1) bad.push(`${token} renders as ${[...vals].sort().join(' AND ')}`);
      }
      expect(checked, `${file}: no undefined-with-fallback tokens were found to judge`)
        .toBeGreaterThan(3);
      expect(bad, `${file}: one token, several colours: ` + bad.join(' | ')).toEqual([]);
    });
  }

  test('★★ the elevation aliases stay ordered — a raised surface must not be darker', async () => {
    const s = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    const hex = (t: string) => {
      const m = new RegExp(String.raw`${t}\s*:\s*(#[0-9a-fA-F]{6})`).exec(s);
      return m ? m[1] : null;
    };
    const lum = (h: string) => {
      const n = parseInt(h.slice(1), 16);
      return ((n >> 16 & 255) * 0.299 + (n >> 8 & 255) * 0.587 + (n & 255) * 0.114);
    };
    const s0 = hex('--surface'), s2 = hex('--surface-2');
    expect(s0, '--surface is not a plain hex any more').not.toBeNull();
    expect(s2, '--surface-2 is not a plain hex any more').not.toBeNull();
    // --bg-elev0 aliases --surface and --bg-elev1 aliases --surface-2; if that ladder ever
    // inverts, every card built on it reads as sunken instead of raised
    expect(lum(s2!), `--surface-2 (${s2}) must be lighter than --surface (${s0})`)
      .toBeGreaterThan(lum(s0!));
  });
});
