import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1599 — TWO GUARDS THAT WERE PROMISES NOBODY KEPT.
//
// `typeof X === 'function'` reads as defensive. It is only defensive if X exists somewhere. When it
// does not, the guard is permanently false and the branch behind it is decoration — and because the
// code still *works* (it falls through, or does nothing visible), nothing ever complains.
//
//   renderAll  — five call sites, declared NOWHERE. Not merely dead: every one of those five sites
//                MUTATES `owned`, and the repaints they do run cover the vault and journal only. The
//                grail meter, hero, boss cards, calculator and both forge tallies kept showing the
//                pre-change picture. That is the "it still shows the old thing" class.
//   uiPrompt    — one call site, declared NOWHERE, so the ternary always took `prompt()` — the exact
//                OS-native white box that uiConfirm was written in v341.41 to replace.
//
// These tests assert the promises are now KEPT, and — more importantly — that the repaint actually
// repaints. A test that only checks `typeof window._repaintOwned === 'function'` would pass on a
// stub that does nothing, which is the same failure one layer up.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2200);
}

test.describe('v1599 — the guards that guarded nothing', () => {
  test('★ the ownership repaint EXISTS and calls the surfaces that show ownership', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      if (typeof w._repaintOwned !== 'function') return { missing: true };
      // Count real invocations rather than trusting the source: a repaint that is wired but never
      // reaches its painters is exactly the defect this replaced.
      const hit: string[] = [];
      const names = ['renderHero', 'renderBossCards', 'renderCalc', 'renderGrailProgress',
                     'renderForgeUni', 'renderForgeSets'];
      const orig: any = {};
      for (const n of names) {
        orig[n] = w[n];
        if (typeof w[n] === 'function') w[n] = () => { hit.push(n); };
      }
      try { w._repaintOwned(); } finally { for (const n of names) w[n] = orig[n]; }
      return { missing: false, hit };
    });
    expect(r.missing, '_repaintOwned must exist — five call sites depend on it').toBe(false);
    expect(r.hit!.length,
      'the repaint reached none of the ownership surfaces — a wired painter that paints nothing is ' +
      'the same bug as the dead guard it replaced').toBeGreaterThanOrEqual(4);
    expect(r.hit).toContain('renderGrailProgress');
  });

  test('★ one painter throwing does NOT stop the others', async ({ page }) => {
    // The state change (a delete, a reset, an intake) has already happened by the time these run.
    // A repaint that aborts halfway would leave a WORSE picture than no repaint: half the surfaces
    // updated, half stale, and no error surfaced to say so.
    await board(page);
    const hit = await page.evaluate(() => {
      const w: any = window;
      const seen: string[] = [];
      const orig = { h: w.renderHero, g: w.renderGrailProgress };
      w.renderHero = () => { throw new Error('boom'); };
      w.renderGrailProgress = () => { seen.push('grail'); };
      try { w._repaintOwned(); } catch (e) { seen.push('ESCAPED'); }
      w.renderHero = orig.h; w.renderGrailProgress = orig.g;
      return seen;
    });
    expect(hit, 'a throwing painter escaped and killed the rest of the repaint').not.toContain('ESCAPED');
    expect(hit, 'the painters after the throwing one must still run').toContain('grail');
  });

  test('★ no `typeof renderAll` guard survives — it was never a function', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => ({
      renderAllExists: typeof (window as any).renderAll,
      // the five sites now call the real thing
      repaint: typeof (window as any)._repaintOwned,
    }));
    expect(r.renderAllExists, 'renderAll was never declared — nothing should pretend to call it')
      .toBe('undefined');
    expect(r.repaint).toBe('function');
  });

  test('★ uiPrompt exists, so the themed dialog family is complete', async ({ page }) => {
    await board(page);
    expect(await page.evaluate(() => typeof (window as any).uiPrompt)).toBe('function');
    expect(await page.evaluate(() => typeof (window as any).uiConfirm)).toBe('function');
  });

  test('★ uiPrompt renders a real focused input and resolves what was typed', async ({ page }) => {
    await board(page);
    const shown = await page.evaluate(() => {
      const w: any = window;
      w.__p = w.uiPrompt('Who is logging these uploads?', 'Konyo');
      return new Promise((res) => setTimeout(() => {
        const inp = document.querySelector('.ui-prompt-input') as HTMLInputElement | null;
        res({
          present: !!inp,
          value: inp ? inp.value : null,
          focused: document.activeElement === inp,
          // it must LOOK like the app, not like an OS box
          themed: !!document.querySelector('.ui-confirm-ov .ui-confirm'),
        });
      }, 350));
    });
    expect(shown).toMatchObject({ present: true, value: 'Konyo', themed: true });
    expect((shown as any).focused, 'the field must be focused — a prompt you have to click first is worse than the native one').toBe(true);

    const typed = await page.evaluate(async () => {
      const w: any = window;
      const inp = document.querySelector('.ui-prompt-input') as HTMLInputElement;
      inp.value = 'Dean';
      (document.querySelector('.ui-confirm-ok') as HTMLButtonElement).click();
      return await w.__p;
    });
    expect(typed, 'OK must resolve the typed value').toBe('Dean');
  });

  test('★ Esc resolves NULL — the caller checks `if (nm != null)`', async ({ page }) => {
    await board(page);
    const out = await page.evaluate(async () => {
      const w: any = window;
      const p = w.uiPrompt('name?', 'Konyo');
      await new Promise((r) => setTimeout(r, 250));
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      return await p;
    });
    expect(out,
      'cancel must be null, not "" — window.setIntakeLogger coerces empty to "Konyo", so returning ' +
      'an empty string on cancel would silently RENAME the logger instead of leaving it alone')
      .toBeNull();
  });

  test('the prompt cleans itself up — no orphaned overlay left in the DOM', async ({ page }) => {
    await board(page);
    const left = await page.evaluate(async () => {
      const w: any = window;
      const p = w.uiPrompt('x', 'y');
      await new Promise((r) => setTimeout(r, 200));
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      await p;
      await new Promise((r) => setTimeout(r, 400));
      return document.querySelectorAll('.ui-confirm-ov').length;
    });
    expect(left, 'a stacked invisible overlay eats clicks on the page beneath it').toBe(0);
  });
});
