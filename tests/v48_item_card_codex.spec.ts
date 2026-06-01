import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v48 — golden item card (renderItemDetailCard, #item-detail-panel) was reading the
// wrong data shapes: ITEM_INFO values are plain strings (no .desc), and BOSS_CHAR_REC
// entries are {top, reason} (no .name/.build/.tip). Result: the "In-Game Stats" block
// never rendered and "Best Character" showed "undefined". Fix wires renderCodexCard
// (ITEM_CODEX) for stats and CHARS[rec.top] for the char card (matches the calc tab).
test.describe('v48 golden item card — in-game stats + best-character render correctly', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('Veil of Steel card shows the ITEM_CODEX stat block (not a broken/empty desc)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderItemDetailCard('Veil of Steel');
      const panel = document.getElementById('item-detail-panel')!;
      return {
        hasCodexCard: !!panel.querySelector('.codex-card'),
        text: panel.innerText,
      };
    });
    expect(r.hasCodexCard).toBe(true);
    expect(r.text).toContain('In-Game Stats');
    expect(r.text).toMatch(/Req Level\s*73/i); // Spired Helm base reqLvl
    expect(r.text).toMatch(/Resist/i);          // +50 all res affix
  });

  test('best-character card uses the CHARS roster — real name/build, never "undefined"', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderItemDetailCard('Veil of Steel');
      const panel = document.getElementById('item-detail-panel')!;
      const nameEl = panel.querySelector('.gic-char-name');
      return {
        section: panel.innerText,
        charName: nameEl ? nameEl.textContent!.trim() : null,
      };
    });
    expect(r.charName).not.toBeNull();
    // resolves to a canonical roster character (Konyolock/Konyodin/Konyoress/Konyossin)
    expect(r.charName!).toMatch(/Konyo(lock|din|ress|ssin)/);
    // build is appended inline from CHARS (e.g. "· Warlock 88")
    expect(r.charName!).toMatch(/·/);
    expect(r.section.toLowerCase()).not.toContain('undefined');
  });

  test('no item produces an "undefined" best-character across a sample of grail items', async ({ page }) => {
    const bad = await page.evaluate(() => {
      const sample = ['Veil of Steel', "Harlequin Crest (Shako)", 'The Stone of Jordan', "Griffon's Eye", 'Tyrael\'s Might'];
      const offenders: string[] = [];
      for (const nm of sample) {
        if (!ITEMS.find((i: any) => i.n === nm)) continue;
        (window as any).renderItemDetailCard(nm);
        const panel = document.getElementById('item-detail-panel')!;
        const charName = panel.querySelector('.gic-char-name')?.textContent || '';
        if (/undefined/i.test(charName)) offenders.push(nm);
      }
      return offenders;
    });
    expect(bad).toEqual([]);
  });
});
