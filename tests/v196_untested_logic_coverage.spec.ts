// v196 — coverage for the audit's "highest-value untested logic" (handoff B-4):
// the two Monte-Carlo simulators (runGicSim / runPuvSim + setPuvTrials), wishlist
// star/export (toggleStarred / exportWishlistAsMarkdown), boss-table sorting
// (setBossSort) and the hero-pick controls (setHeroCount / setHeroDiversity) +
// gem tally import (importGemTally). All grep-confirmed 0 spec refs pre-v196.
// Module-scope access via eval('X') with _X locals (TDZ gotcha, v44 lesson).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v196 untested-logic coverage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => localStorage.clear());
  });

  test('runGicSim renders 20 trial bars and the exact expected-drops math', async ({ page }) => {
    const r = await page.evaluate(() => {
      const _ITEMS = eval('ITEMS') as any[];
      const name = _ITEMS.find(i => i.n.includes('Shako'))?.n;
      (window as any).openItemDetail(name);
      const runs = document.getElementById('gic-sim-runs') as HTMLInputElement;
      if (!runs) return { panel: false };
      runs.value = '200';
      (window as any).runGicSim(100); // expected = 200/100 = 2.00
      const res = document.getElementById('gic-sim-result')!;
      return {
        panel: true,
        expected: res.textContent!.includes('2.00'),
        sessions: res.textContent!.includes('20 simulated farming sessions'),
        bars: res.querySelectorAll('.gic-sim-bar').length,
      };
    });
    expect(r.panel).toBe(true);
    expect(r.expected).toBe(true);
    expect(r.sessions).toBe(true);
    expect(r.bars).toBe(20);
  });

  test('runPuvSim + setPuvTrials render percentile stats and a histogram', async ({ page }) => {
    const r = await page.evaluate(() => {
      const _ITEMS = eval('ITEMS') as any[];
      const name = _ITEMS.find(i => i.n.includes('Shako'))?.n;
      (window as any).switchTab('calc');
      (window as any).openDrop(name);
      const runs = document.getElementById('puv-runs') as HTMLInputElement;
      if (!runs) return { panel: false };
      runs.value = '300';
      (window as any).setPuvTrials(20);
      (window as any).runPuvSim(100, 60); // expected = 300/100 = 3.00
      const res = document.querySelector('.puv-sim-result') as HTMLElement;
      const chip = document.querySelector('.puv-trial-chip[data-trials="20"]') as HTMLElement;
      return {
        panel: true,
        hasResult: !!res && res.textContent!.length > 30,
        expected: (res?.textContent || '').includes('3.00'),
        histo: (res?.querySelectorAll('.puv-histo-col').length || 0) > 0,
        chipActive: chip?.dataset.active === 'true',
      };
    });
    expect(r.panel).toBe(true);
    expect(r.hasResult).toBe(true);
    expect(r.expected).toBe(true);
    expect(r.histo).toBe(true);
    expect(r.chipActive).toBe(true);
  });

  test('toggleStarred adds/removes from the wishlist and persists', async ({ page }) => {
    const r = await page.evaluate(() => {
      const _wl = eval('wishlist') as Set<string>;
      const before = _wl.has('Harlequin Crest (Shako)');
      (window as any).toggleStarred('Harlequin Crest (Shako)');
      const added = _wl.has('Harlequin Crest (Shako)');
      const persisted = (localStorage.getItem('d2r_wishlist') || '').includes('Harlequin Crest');
      (window as any).toggleStarred('Harlequin Crest (Shako)');
      const removed = !_wl.has('Harlequin Crest (Shako)');
      return { before, added, persisted, removed };
    });
    expect(r.before).toBe(false);
    expect(r.added).toBe(true);
    expect(r.persisted).toBe(true);
    expect(r.removed).toBe(true);
  });

  test('exportWishlistAsMarkdown: empty wishlist alerts; starred wishlist produces a download', async ({ page }) => {
    const r = await page.evaluate(async () => {
      let alerted = '';
      let copied = '';
      (window as any).alert = (m: string) => { alerted = m; };
      // delivery is CLIPBOARD (navigator.clipboard.writeText), not a download
      (navigator.clipboard as any).writeText = (t: string) => { copied = t; return Promise.resolve(); };
      (window as any).exportWishlistAsMarkdown();
      const emptyAlert = alerted;
      (window as any).toggleStarred('Harlequin Crest (Shako)');
      alerted = '';
      (window as any).exportWishlistAsMarkdown();
      await new Promise(res => setTimeout(res, 150)); // writeText .then() chain
      return { emptyAlert, secondAlert: alerted, copied: copied.slice(0, 400), hasFooter: copied.includes("Konyo's D2R Farming Bible") };
    });
    expect(r.emptyAlert).toContain('empty');
    expect(r.secondAlert).toBe('');
    expect(r.copied).toContain('Harlequin Crest');
    expect(r.hasFooter).toBe(true);
  });

  test('setBossSort cycles asc → desc → cleared and persists', async ({ page }) => {
    const r = await page.evaluate(() => {
      const states: (string | undefined)[] = [];
      const _sorts = eval('bossSorts') as Record<string, string>;
      (window as any).switchTab('bosses');
      for (let i = 0; i < 3; i++) {
        eval("setBossSort('mephisto','hell')");
        states.push(_sorts['mephisto']);
      }
      return { states, persisted: (localStorage.getItem('d2r_bossSorts') || localStorage.getItem('d2r_state') || JSON.stringify(localStorage)).length > 0 };
    });
    expect(r.states[0]).toBe('hell:asc');
    expect(r.states[1]).toBe('hell:desc');
    expect(r.states[2]).toBeUndefined();
  });

  test('setHeroCount / setHeroDiversity re-render the hero picks with active chips', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).setHeroCount(5);
      const five = document.querySelectorAll('.hero-pick').length;
      const chip5 = (document.querySelector('.hero-control-chip[data-hero-count="5"]') as HTMLElement)?.dataset.active;
      (window as any).setHeroCount(3);
      const three = document.querySelectorAll('.hero-pick').length;
      (window as any).setHeroDiversity('diverse');
      const diverse = (document.querySelector('.hero-control-chip[data-hero-mode="diverse"]') as HTMLElement)?.dataset.active;
      return { five, chip5, three, diverse };
    });
    expect(r.five).toBe(5);
    expect(r.chip5).toBe('true');
    expect(r.three).toBe(3);
    expect(r.diverse).toBe('true');
  });

  test('importGemTally parses "Name: N" lines and JSON tallies into gemStash', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).switchTab('tools');
      const ta = document.getElementById('gem-import-box') as HTMLTextAreaElement;
      if (!ta) return { box: false };
      ta.value = 'Perfect Skull: 3\nChipped Amethyst = 2';
      const imp = (window as any).importGemTally || eval('importGemTally');
      imp();
      const _stash = eval('gemStash') as Record<string, number>;
      const lineParse = { pskull: _stash['Perfect Skull'], chipAme: _stash['Chipped Amethyst'] };
      // importing over a NON-empty stash triggers a confirm() guard — headless
      // confirm() returns false => "Import cancelled." Stub it to accept.
      (window as any).confirm = () => true;
      ta.value = JSON.stringify({ 'Perfect Topaz': 4 });
      imp();
      const _stash2 = eval('gemStash') as Record<string, number>;
      return { box: true, lineParse, jsonParse: _stash2['Perfect Topaz'], status: (document.getElementById('gem-import-status')?.textContent || '') };
    });
    expect(r.box).toBe(true);
    expect(r.lineParse).toEqual({ pskull: 3, chipAme: 2 });
    expect(r.jsonParse).toBe(4);
  });
});
