import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1562 — THREE THINGS THAT COULD NEVER HAVE WORKED.
//
// All three are the same shape as REG-083 and REG-087: a name that reads as available from where it
// is used, and is declared somewhere that use cannot reach — or, in one case, was never declared at
// all. `typeof` on an undeclared name does not throw. It returns 'undefined', the guard is
// permanently false, and the feature silently does nothing forever.
//
//   1. the Session cockpit's SETS tile guarded on `typeof SETS` — there is no SETS in the file
//      (the array is ITEM_SETS), so the tile has never rendered once
//   2. window.setIntakeLogger refreshes the 👤 badge behind `typeof renderJournal === 'function'`,
//      and renderJournal lives inside the vault IIFE with no export
//   3. the live-visit chronicle path never stored its proposal, so ⚖ tune the gate appeared and
//      could only answer "no sweep evidence in memory"

const boot = async (page: any) => { await page.goto(URL); await page.waitForTimeout(2200); };

test.describe('v1562 — three dead seams', () => {
  test('★ the SETS name the guard wanted never existed', async () => {
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    expect(src, 'the dead guard must be gone').not.toContain("typeof SETS!=='undefined'");
    expect(/\b(const|let|var)\s+SETS\s*=/.test(src),
      'and it must not be "fixed" by inventing the name it wanted').toBe(false);
  });

  test('★ the Session cockpit now reports SETS, from the same seam F·Sets uses', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.renderSessionCockpit && w.renderSessionCockpit();
      const kpis = document.getElementById('sc-kpis');
      const txt = (kpis && kpis.textContent) || '';
      const fs2 = w.fsetsScan();
      return { txt, pair: fs2.havePieces + '/' + fs2.totalPieces, tiles: kpis ? kpis.children.length : 0 };
    });
    expect(r.tiles, 'the cockpit had four tiles and no Sets tile').toBeGreaterThanOrEqual(5);
    expect(r.txt, 'and it must show the SAME pair F·Sets shows, not a second denominator')
      .toContain(r.pair);
  });

  test('★ renderJournal is reachable from the block that guards on it', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => ({
      journal: typeof (window as any).renderJournal,
      setter: typeof (window as any).setIntakeLogger,
    }));
    expect(r.journal, 'the guard in setIntakeLogger needs this to resolve').toBe('function');
    expect(r.setter).toBe('function');
  });

  test('★ THE RENAME: the badge follows the value, instead of disagreeing with it', async ({ page }) => {
    // the badge is live-rendered from intakeLogger on every renderJournal(), so the refresh IS the
    // display. Persisted correctly + never repainted = "it looks like it failed, so do it again",
    // while every intake from that moment is already tagged with the new name.
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      // do NOT hand-build a journal row — its shape is the vault's business and guessing it wrong
      // makes this a test of my fixture rather than of the refresh. Drive the real seam and watch
      // whether the render is REACHED.
      let painted = 0;
      const real = w.renderJournal;
      w.renderJournal = function () { painted += 1; try { return real.apply(this, arguments); } catch (e) { return null; } };
      w.setIntakeLogger('Cousin');
      const stored = w.getIntakeLogger ? w.getIntakeLogger() : null;
      w.renderJournal = real;
      return { painted, stored };
    });
    expect(r.stored, 'the value always persisted — that was never the bug').toBe('Cousin');
    expect(r.painted, 'the rename must REACH the render, which is what draws the badge')
      .toBeGreaterThan(0);
  });

  test('★ the live-visit path stores its evidence, so the gate tuner is not a dead button', async () => {
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_app.py'), 'utf8');
    const writes = (src.match(/globals\(\)\["_CHRON_LAST_PROPOSAL"\] = prop/g) || []).length;
    expect(writes, 'both the retro sweep AND the live visit must record their proposal').toBe(2);
    // and the visit write must sit with the visit's own proposal, not be a stray copy
    const visit = src.slice(src.indexOf('def _chron_visit_run'), src.indexOf('def _chron_sweep_run'));
    expect(visit, 'the visit path writes its own').toContain('_CHRON_LAST_PROPOSAL');
  });
});
