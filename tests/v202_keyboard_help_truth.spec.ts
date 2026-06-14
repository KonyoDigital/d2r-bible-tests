// v202 — keyboard + help-legend truth pass (Konyo: "the legend needs fixing,
// I want the B and D to work"). B was gated behind keyboard-focus on a calc
// tile (click-selecting then pressing B did nothing) — now global with a
// selected/active item. Tab keys extended 9=endgame 0=tools; the palette's
// index-derived hints LIED for endgame/binds/ref (said 7/8/9, real keys are
// binds=7 ref=8 endgame=9) — now read from the canonical key map. Help modal
// rewritten to truth (source-strip is the aid-card chips since v38; two sims).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v202 keyboard + help truth', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
  });

  // v282: digit shortcuts follow the visual tab order — 7=endgame, 8=binds, 9=reference, 0=tools.
  test('keys 7/8/9/0 switch to endgame/binds/reference/tools (visual order)', async ({ page }) => {
    const active = () => page.evaluate(() => (document.querySelector('.tabs .tab.active') as HTMLElement)?.dataset.tab);
    await page.keyboard.press('7'); await page.waitForTimeout(200);
    expect(await active()).toBe('endgame');
    await page.keyboard.press('8'); await page.waitForTimeout(200);
    expect(await active()).toBe('binds');
    await page.keyboard.press('9'); await page.waitForTimeout(200);
    expect(await active()).toBe('ref');
    await page.keyboard.press('0'); await page.waitForTimeout(200);
    expect(await active()).toBe('tools');
  });

  test('B works from ANY tab once an item is selected: jump + bar + glow/dim; Esc clears', async ({ page }) => {
    await page.keyboard.press('2');
    await page.waitForTimeout(400);
    await page.evaluate(() => (document.querySelector('.item-tile') as HTMLElement).click());
    await page.waitForTimeout(300);
    await page.keyboard.press('4'); // wander off to runes
    await page.waitForTimeout(250);
    await page.keyboard.press('b');
    await page.waitForTimeout(700);
    const r = await page.evaluate(() => ({
      tab: (document.querySelector('.tabs .tab.active') as HTMLElement)?.dataset.tab,
      bar: document.getElementById('active-item-bar')?.classList.contains('show'),
      glow: document.querySelectorAll('.boss-card.has-item').length,
      dim: document.querySelectorAll('.boss-card.no-item').length,
    }));
    expect(r.tab).toBe('bosses');
    expect(r.bar).toBe(true);
    expect(r.glow).toBeGreaterThanOrEqual(1);
    expect(r.dim).toBeGreaterThanOrEqual(1);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const after = await page.evaluate(() => ({
      bar: document.getElementById('active-item-bar')?.classList.contains('show'),
      glow: document.querySelectorAll('.boss-card.has-item').length,
    }));
    expect(after.bar).toBe(false);
    expect(after.glow).toBe(0);
  });

  test('palette tab hints match the REAL key map (endgame=7, binds=8, ref=9, tools=0)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any)._v42_openPalette();
      const input = document.querySelector('#v42-palette-input') as HTMLInputElement;
      const hintFor = (q: string, label: string) => {
        input.value = q;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const item = [...document.querySelectorAll('#v42-palette-list .v42-pal-item')]
          .find(e => (e.querySelector('.v42-pal-label')?.textContent || '').startsWith(label));
        // the hint renders inside a .v42-pal-category span (c.hint branch)
        return [...(item?.querySelectorAll('.v42-pal-category') || [])]
          .map(e => (e.textContent || '').trim()).find(t => /^[0-9]$/.test(t)) || '';
      };
      return {
        binds: hintFor('binds', 'Switch to Binds'),
        ref: hintFor('reference', 'Switch to Reference'),
        endgame: hintFor('endgame', 'Switch to Endgame'),
        tools: hintFor('tools', 'Switch to Tools'),
      };
    });
    expect(r.endgame).toBe('7');
    expect(r.binds).toBe('8');
    expect(r.ref).toBe('9');
    expect(r.tools).toBe('0');
  });

  test('help modal tells the truth: no stale v12/1-7 claims, B-anywhere, chips not source-strip', async ({ page }) => {
    const r = await page.evaluate(() => {
      const help = document.getElementById('help-modal')!.textContent!;
      const hint = document.getElementById('shortcut-hint')!.textContent!;
      return {
        noV12Kbd: !help.includes('Keyboard shortcuts (v12)'),
        tabsLine: help.includes('7=endgame') && help.includes('0=tools') && help.includes('8=binds'),
        bAnywhere: help.includes('from ANY tab'),
        noSourceStrip: !help.includes('source-strip'),
        chips: help.includes('one-click chips'),
        hintBadge: hint.includes('1-9·0'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });
});
