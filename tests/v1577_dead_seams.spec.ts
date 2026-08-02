import { test, expect } from './_net_stub';
import * as path from 'path';
import * as fs from 'fs';

const FILE = path.resolve(__dirname, '..', 'bible.html');
const URL = 'file://' + FILE;

// v1577 — THE DEAD-SEAM INVARIANT: a guard that can never be true is not a safety net, it is a
// deleted feature that still looks present in the source.
//
// The class, in Konyo's board's own words: plumbing with no tap. Code declared, read, cleared, and
// described in a commit message as a working feature, that nothing ever calls or nothing ever writes.
// The population found by the v1576 sweep:
//
//   · `typeof toast === 'function'`     — v631 forge-base promotion. `toast` is declared NOWHERE in
//                                         38k lines, so the promotion NEVER once announced itself,
//                                         while really promoting reads (["Heater (2 os)"]).
//   · `window._toast && window._toast()` — the Vault "🪄 Fix all safe" button. No writer anywhere.
//                                         It repaired N issues and gave zero receipt. The && ate it.
//   · `typeof escHtml === 'function'`    — fell through to a fallback that did NOT escape, into a
//                                         data-n attribute that ↩ undo reads back. A grail name with
//                                         a quote in it would have un-ticked the WRONG grail.
//   · `window._FORGE_REDO`               — mine, v1570. Declared, read, cleared. Never written.
//
// WHY THIS SPEC IS AN EXECUTION TEST AND NOT A GREP: the first sweep briefed the fleet that a
// `typeof NAME` guard in a DIFFERENT <script> block is dead. That is FALSE — top-level let/const in
// classic scripts share one global lexical environment across the whole document, so 190 of 196
// guarded names in this file are perfectly live and a grep-based detector would have condemned them
// all. The only thing that distinguishes a dead guard from a live one is asking a REAL BROWSER,
// after the page has fully booted, whether the name resolves. So that is what this does.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(1800);
}

/**
 * Names that resolve to nothing and are KNOWINGLY left that way. Every entry needs a reason and an
 * owner — an allowlist without one is just a way to make a red spec quiet.
 *
 * These three are PARKED FOR KONYO because the fix is a product decision, not a repair:
 */
const PARKED: Record<string, string> = {
  renderAll:
    'five call sites (bible.html 16916/29618/30265/30711/31309), all permanent no-ops. There is no ' +
    'renderAll — there are ~30 individual window.renderX functions. WHICH of them it should fan out ' +
    'to is a product call. Mitigating: every site already calls explicit renderers immediately ' +
    'before it, so this is likely dead weight rather than missing behaviour. Wire it or delete it.',
  uiPrompt:
    'bible.html:14962 — the styled-dialog upgrade was never built, so the intake-logger name prompt ' +
    'always falls back to the native browser prompt(). It WORKS; it is just not the promised dialog.',
  escHtml:
    'bible.html:19590 — the SECOND escHtml ternary. Unlike the one fixed in v1576 (which fell ' +
    'through to a no-op and was an injection route), this fallback really does escape & < > ", so ' +
    'the dead guard is harmless here. Kept visible rather than silently deleted.',
};

test.describe('v1577 — no guard may be permanently false', () => {
  test('★ every `typeof NAME` guard in bible.html names something that actually exists', async ({ page }) => {
    await board(page);

    const src = fs.readFileSync(FILE, 'utf8');
    // Only real guards: `typeof X === 'function'` / `!== 'undefined'` etc. Skip `typeof window.X`
    // (a property read that is legal even when absent) and anything inside a // comment line.
    const names = new Set<string>();
    for (const line of src.split('\n')) {
      if (/^\s*(\/\/|\*|<!--)/.test(line)) continue;
      for (const m of line.matchAll(/typeof\s+([A-Za-z_$][\w$]*)\s*(===|!==|==|!=)\s*['"]/g)) {
        const n = m[1];
        if (n === 'window' || n === 'document' || n === 'undefined') continue;
        names.add(n);
      }
    }
    expect(names.size, 'the detector itself must not silently match nothing').toBeGreaterThan(50);

    // TWO independent witnesses, because either one alone lies in a different direction.
    //
    // Witness 1 — the live page. Ask a real browser, after boot, whether the name resolves at global
    // scope. This is what proves the fleet's original premise wrong: 190 of 196 cross-block names DO
    // resolve, because classic scripts share one global lexical environment.
    //
    // Witness 2 — the source. A `typeof v === 'function'` check on a FUNCTION-LOCAL variable is
    // perfectly live at its own site and invisible to witness 1, which sees only global scope. On the
    // first run this spec flagged 26 such names (v, d, h, map, meta, _fArt, refreshOpenCard…) and
    // every one of them turned out to be declared somewhere as a local or a nested function.
    //
    // So a name is condemned only when BOTH agree: it resolves nowhere at runtime AND it is declared
    // nowhere in the file. That is the exact shape of every genuine instance found so far — toast,
    // _toast, escHtml, renderAll, uiPrompt were all declared NOWHERE, not merely out of scope.
    //
    // HONEST LIMIT, stated rather than hidden: this does NOT catch a name whose sole declaration is
    // nested inside an IIFE while the guard sits outside it (the REG-083/087 shape). Distinguishing
    // that from a healthy local needs a real scope analysis, not a regex, and a detector that guesses
    // would either condemn ~26 healthy names or quietly pass everything. The v1576 scope map found
    // zero live instances of that shape; if one ever appears, it will need a parser, not this spec.
    const declaredSomewhere = (n: string) => {
      const e = n.replace(/[$]/g, '\\$');
      return new RegExp(
        `function\\s+${e}\\s*\\(|` +               // function decl (incl. nested)
        `\\b(?:var|let|const)\\s+${e}\\s*[=;,)]|` + // any binding, any scope
        `window\\.${e}\\s*=|` +                     // global assignment
        `\\b${e}\\s*:\\s*function|` +               // object-literal method
        `function\\s*[\\w$]*\\s*\\([^)]*\\b${e}\\b[^)]*\\)`, // parameter
      ).test(src);
    };

    const unresolved: string[] = await page.evaluate((list: string[]) => {
      const dead: string[] = [];
      for (const n of list) {
        let ok = false;
        try { ok = eval('typeof ' + n) !== 'undefined'; } catch (e) { ok = false; }
        if (!ok) dead.push(n);
      }
      return dead;
    }, [...names]);

    const declaredNowhere = unresolved.filter((n) => !declaredSomewhere(n));
    const unexpected = declaredNowhere.filter((n) => !(n in PARKED));
    expect(unexpected,
      'these guards can NEVER be true — the branch behind each is a feature that looks shipped and ' +
      'does nothing. Either point the guard at the real name, or delete the branch.\n' +
      'Dead names: ' + JSON.stringify(unexpected)).toEqual([]);
  });

  test('the PARKED list is honest — every name on it really is still dead', async ({ page }) => {
    // An allowlist that outlives its reason is how a real bug becomes permanent. If one of these has
    // since been implemented, this fails and forces the entry out of the list.
    await board(page);
    const src = fs.readFileSync(FILE, 'utf8');
    const stillDead: string[] = await page.evaluate((list: string[]) => {
      const dead: string[] = [];
      for (const n of list) {
        let ok = false;
        try { ok = eval('typeof ' + n) !== 'undefined'; } catch (e) { ok = false; }
        if (!ok) dead.push(n);
      }
      return dead;
    }, Object.keys(PARKED));
    expect(stillDead.sort(),
      'a PARKED name now resolves — it was implemented. Remove it from PARKED.').toEqual(Object.keys(PARKED).sort());

    // and still declared nowhere — if someone writes the function but the guard stops matching for
    // another reason, the entry is stale either way.
    for (const n of Object.keys(PARKED)) {
      expect(new RegExp(`function\\s+${n}\\s*\\(|window\\.${n}\\s*=`).test(src),
        `${n} now has a declaration — remove it from PARKED (reason on file: ${PARKED[n]})`).toBe(false);
    }
  });

  test('★ the v1576 repairs are still wired: the toast the board actually owns', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        grailToast: typeof w._grailToast,
        // the two names the repairs replaced — proven absent so a revert cannot pass quietly
        toast: typeof (w as any).toast,
        _toast: typeof w._toast,
        promote: typeof w._promoteUnknownBases,
      };
    });
    expect(r.grailToast, 'the real toast must be on window for the repaired call sites').toBe('function');
    expect(r._toast, 'window._toast has no writer anywhere in the repo — it must stay absent').toBe('undefined');
    expect(r.promote, 'the v631 promotion that never announced itself must still exist').toBe('function');
  });

  test('★ window._FORGE_REDO is written by undo, not merely declared (v1570 shipped it dead)', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      return { slot: '_FORGE_REDO' in w, undo: typeof w._forgeUndo, redo: typeof w._forgeRedo };
    });
    expect(r.slot, 'the redo slot must exist').toBe(true);
    expect(r.undo, 'SOMETHING must write the slot — a slot with no writer is the v1570 bug').toBe('function');
    expect(r.redo, 'and something must read it back').toBe('function');
  });
});
