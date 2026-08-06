import { test, expect } from './_net_stub';
import * as path from 'path';

// v1686 — NO ID-SCOPED OVERRIDE MAY LOSE ON SOURCE ORDER ALONE.
//
// v1685 cost three versions to a defect that looked fixed in every diff: v1672 added
// `#tab-forge .forge-title{color:var(--q-runeword)}` and wrote a commit message describing the new
// colour, but the rule never painted. `:is(#tab-forge,#tab-funi,#tab-fsets) .forge-title` has the
// SAME specificity — :is() takes its most specific argument, an id, so both are (1,1,0) — and is
// written LATER, so source order took it. Its two siblings looked correct only because their
// overrides happen to sit after that rule. The repo already knows this trap by name (LAST RULE
// WINS; `.hero-title` had four rules and editing the first was inert), and knowing it by name has
// not been enough: it has now landed at least twice.
//
// So this gate looks for the SHAPE rather than for any particular rule. For every element that a
// single-#id-scoped rule sets `color` on — an id scope is somebody saying "this one place is
// different", i.e. an intent override — it finds every matching color rule, computes specificity,
// and flags the case where the winner beats the intent rule with EQUAL specificity purely by being
// written later.
//
// WHAT IT DELIBERATELY DOES NOT FLAG, each one measured as a false positive while writing this:
//   · A winner with HIGHER specificity. `#tab-session .sc-tag.want` beating `#tab-session .sc-tag`
//     is a state class doing its job, not an accident.
//   · `!important`. That is a different mechanism and always deliberate.
//   · A rule whose value is `var(--x, fallback)` where --x resolves. `#tab-tools .tqu-txt b` reads
//     var(--a,#f2ead8) and computes gold because --a is set on an ancestor — working as designed.
// Without those three exclusions this reported five hits and four were noise. A gate that cries
// wolf is deleted within a month, which is worse than not having one.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// every tab, so id-scoped rules have live elements to match against
const TABS = ['main', 'bosses', 'calc', 'tz', 'tztracker', 'runes', 'rotw', 'ancients',
              'endgame', 'binds', 'ref', 'tools', 'forge', 'funi', 'fsets', 'session'];

test('★★★ no #id-scoped colour override is beaten on source order alone', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction(() => typeof (window as any).switchTab === 'function', null, { timeout: 20000 });
  for (const t of TABS) {
    await page.evaluate((x) => { try { (window as any).switchTab(x); } catch (e) { /* noop */ } }, t);
    await page.waitForTimeout(90);
  }
  await page.waitForTimeout(400);

  const hits = await page.evaluate(() => {
    /* Specificity as [id, class, type]. Good enough for this file's vocabulary, and — the part that
       matters — :is()/:where() are handled the way the cascade actually handles them: :is() takes
       its most specific argument, :where() always contributes zero. Getting that wrong is precisely
       how the v1685 rule looked like it should win. */
    const spec = (sel: string): [number, number, number] => {
      let s = sel;
      let extra: [number, number, number] = [0, 0, 0];
      s = s.replace(/:where\([^()]*\)/g, ' ');
      s = s.replace(/:is\(([^()]*)\)/g, (_m, inner: string) => {
        let best: [number, number, number] = [0, 0, 0];
        for (const part of inner.split(',')) {
          const c: [number, number, number] = [
            (part.match(/#[\w-]+/g) || []).length,
            (part.match(/\.[\w-]+/g) || []).length + (part.match(/\[[^\]]*\]/g) || []).length,
            (part.match(/(^|[\s>+~])[a-zA-Z][\w-]*/g) || []).length];
          if (c[0] !== best[0] ? c[0] > best[0] : c[1] !== best[1] ? c[1] > best[1] : c[2] > best[2]) best = c;
        }
        extra = [extra[0] + best[0], extra[1] + best[1], extra[2] + best[2]];
        return ' ';
      });
      return [(s.match(/#[\w-]+/g) || []).length + extra[0],
              (s.match(/\.[\w-]+/g) || []).length + (s.match(/\[[^\]]*\]/g) || []).length
                + (s.match(/:(?!:)[\w-]+/g) || []).length + extra[1],
              (s.match(/(^|[\s>+~])[a-zA-Z][\w-]*/g) || []).length + extra[2]];
    };
    const cmp = (a: number[], b: number[]) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2];

    /* ⚠ SPLIT ON TOP-LEVEL COMMAS ONLY. My first version did `selectorText.split(',')`, which
       shatters `:is(#tab-forge,#tab-funi,#tab-fsets) .forge-title` into ':is(#tab-forge',
       '#tab-funi' and '#tab-fsets) .forge-title' — the first two throw in el.matches() and the
       third matches nothing. The result: the gate ran clean against a tree with the v1685 defect
       deliberately reintroduced, because the rule that does the beating had been shredded before
       it could be compared. Caught by re-running the red case rather than by reading the code. */
    const splitTop = (sel: string): string[] => {
      const out: string[] = [];
      let depth = 0, buf = '';
      for (const ch of sel) {
        if (ch === '(' || ch === '[') depth++;
        else if (ch === ')' || ch === ']') depth--;
        if (ch === ',' && depth === 0) { out.push(buf.trim()); buf = ''; continue; }
        buf += ch;
      }
      if (buf.trim()) out.push(buf.trim());
      return out;
    };

    // collect every color-setting rule once, in document order
    type R = { sel: string; val: string; important: boolean; sp: [number, number, number]; i: number };
    const rules: R[] = [];
    let i = 0;
    for (const sheet of document.styleSheets) {
      let rs: CSSRuleList | null = null;
      try { rs = (sheet as CSSStyleSheet).cssRules; } catch (e) { continue; }
      if (!rs) continue;
      for (const r of rs as any) {
        if (!r.selectorText || !r.style) continue;
        const val = r.style.getPropertyValue('color');
        if (!val) continue;
        for (const one of splitTop(String(r.selectorText))) {
          const sel = one.trim();
          if (sel) rules.push({ sel, val, important: r.style.getPropertyPriority('color') === 'important',
                                sp: spec(sel), i: i++ });
        }
      }
    }

    const out: any[] = [];
    const seen = new Set<string>();
    for (const intent of rules) {
      // an intent override = scoped to exactly one #id, and not itself a state variant
      if (!/^#[\w-]+[\s.>]/.test(intent.sel)) continue;
      if (intent.important) continue;
      let els: Element[] = [];
      try { els = [...document.querySelectorAll(intent.sel)]; } catch (e) { continue; }
      const el = els.find((e) => (e as HTMLElement).offsetParent !== null) || els[0];
      if (!el) continue;

      // the winner among all matching color rules, by the real cascade order
      let win: R | null = null;
      for (const r of rules) {
        let m = false;
        try { m = el.matches(r.sel); } catch (e) { continue; }
        if (!m) continue;
        if (!win) { win = r; continue; }
        if (r.important !== win.important) { if (r.important) win = r; continue; }
        if (cmp(r.sp, win.sp) > 0 || (cmp(r.sp, win.sp) === 0 && r.i > win.i)) win = r;
      }
      if (!win || win === intent || win.important) continue;
      // ONLY the source-order case: equal specificity, written later
      if (cmp(win.sp, intent.sp) !== 0) continue;
      // …and only when it actually changes the painted colour
      const probe = document.createElement('span');
      document.body.appendChild(probe);
      probe.style.color = intent.val;
      const want = getComputedStyle(probe).color;
      probe.remove();
      const got = getComputedStyle(el).color;
      if (got === want) continue;
      const key = intent.sel + '|' + win.sel;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ inert: intent.sel, declared: intent.val, wants: want,
                 beatenBy: win.sel, paints: got, specificity: intent.sp.join(',') });
    }
    return out;
  });

  expect(hits, hits.length
    ? `${hits.length} id-scoped colour override(s) are INERT — same specificity as the rule that `
      + 'beats them, and written earlier, so source order decides. Move each one BELOW the rule '
      + 'named in beatenBy (that is the whole fix — v1685):\n'
      + hits.map((h: any) => `  ${h.inert} {color:${h.declared}} wants ${h.wants} but paints `
                           + `${h.paints} — beaten by ${h.beatenBy} at equal specificity (${h.specificity})`).join('\n')
    : '').toEqual([]);
});
