import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v68 — Rune Stash gets a "what can I make" runeword planner + collapsible card + tally import.
//   1. The runeword recipes (formerly trapped in the search palette IIFE as V42_RUNEWORDS) are
//      promoted to ONE top-level global RUNEWORDS, shared by the search AND the planner. Zero
//      fabrication: the same recipe strings already shipped in the app.
//   2. Planner reads the user's own tally and reports which popular runewords are READY NOW
//      (every rune in hand) vs craftable WITH CUBE-UPS (honest greedy: highest-required rune
//      first, draining a shared pool so shared lowers are never double-counted).
//   3. The card is collapsible — title only until its header is clicked.
//   4. An import box loads a pasted "Name:count" / JSON tally into the stash.
test.describe('v68 rune craft planner + collapse + import', () => {
  test.beforeEach(async ({ page }) => {
    page.on('dialog', (d) => d.accept());
    await page.goto(URL);
    await page.evaluate(() => { try { localStorage.removeItem('d2r_runeStash'); } catch (e) {} });
    await page.reload();
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="runes"]');
    await page.waitForTimeout(150);
  });

  test('the card is collapsible: starts title-only, header click expands and re-collapses', async ({ page }) => {
    const card = page.locator('#rune-stash-card');
    await expect(card).toHaveClass(/collapsed/);                 // default: only the title shows
    // body is hidden while collapsed
    expect(await page.locator('#rune-stash-card .boss-body').isVisible()).toBe(false);
    await page.click('#rune-stash-card .boss-header');
    await page.waitForTimeout(120);
    await expect(card).not.toHaveClass(/collapsed/);
    expect(await page.locator('#rune-stash-card .boss-body').isVisible()).toBe(true);
    const expanded = await page.getAttribute('#rune-stash-card .boss-header', 'aria-expanded');
    expect(expanded).toBe('true');
    await page.click('#rune-stash-card .boss-header');           // toggle shut again
    await page.waitForTimeout(120);
    await expect(card).toHaveClass(/collapsed/);
    expect(await page.locator('#rune-stash-card .boss-body').isVisible()).toBe(false);
  });

  test('RUNEWORDS is one shared global powering both the planner and the search palette', async ({ page }) => {
    const r = await page.evaluate(() => {
      const list = (window as any).RUNEWORDS as any[];
      return {
        type: typeof list,
        len: Array.isArray(list) ? list.length : -1,
        hasEnigma: Array.isArray(list) && list.some((x) => x.n === 'Enigma'),
        fns: ['runeCraftStatus', 'canMakeNow', 'canMakeWithCubing', 'runewordReq', 'importRuneTally', 'toggleCardCollapse', 'renderRuneCraftable']
          .map((n) => typeof (window as any)[n]),
      };
    });
    expect(r.type).toBe('object');
    expect(r.len).toBeGreaterThanOrEqual(15);
    expect(r.hasEnigma).toBe(true);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
    // and the global search still resolves a runeword (proves the shared move didn't break search)
    await page.fill('#gsearch-input', 'enigma');
    await page.waitForTimeout(220);
    const cats = await page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
      .map((el) => ({
        lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
        cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
      })));
    expect(cats.some((x) => /Enigma/.test(x.lab) && x.cat === 'runeword')).toBe(true);
  });

  test('runewordReq parses recipes with multiplicity and rejects non-runeword entries', async ({ page }) => {
    const r = await page.evaluate(() => {
      const list = (window as any).RUNEWORDS as any[];
      const lastWish = list.find((x) => x.n === 'Last Wish');
      const deathsWeb = list.find((x) => /Death's Web/.test(x.n));
      return {
        lw: (window as any).runewordReq(lastWish),
        dw: (window as any).runewordReq(deathsWeb),
      };
    });
    expect(r.lw).toEqual({ Jah: 3, Mal: 1, Sur: 1, Ber: 1 });   // 3× Jah counted, not collapsed to 1
    expect(r.dw).toBeNull();                                     // "(unique, not RW)" -> not craftable
  });

  test('cube-aware predicates are honest (9 El can become a Tir, but not a Nef)', async ({ page }) => {
    const r = await page.evaluate(() => {
      for (let i = 0; i < 9; i++) (window as any).adjustRuneStash('El', 1);   // 9 El → 3 Eld → 1 Tir
      return {
        tirNow: (window as any).canMakeNow({ Tir: 1 }),
        tirCube: (window as any).canMakeWithCubing({ Tir: 1 }),
        eldCube: (window as any).canMakeWithCubing({ Eld: 1 }),
        nefCube: (window as any).canMakeWithCubing({ Nef: 1 }),
        elNow: (window as any).canMakeNow({ El: 3 }),
      };
    });
    expect(r.tirNow).toBe(false);     // you don't hold a Tir
    expect(r.tirCube).toBe(true);     // but 9 El cubes up to exactly one
    expect(r.eldCube).toBe(true);     // 3 of the 9 → an Eld
    expect(r.nefCube).toBe(false);    // 9 El stops at Tir, two rungs short of Nef
    expect(r.elNow).toBe(true);       // and the raw El are in hand
  });

  test('the planner lists the runewords my tally can actually build right now', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ta = document.getElementById('rune-import-box') as HTMLTextAreaElement;
      ta.value = 'Tal:2 Thul:1 Ort:1 Amn:1 Ral:1 Tir:1 Sol:1 Shael:1 Lem:1 Ko:1';
      (window as any).importRuneTally();
      const status = runeCraftStatusNames();
      function runeCraftStatusNames(){
        const s = (window as any).runeCraftStatus();
        return { ready: s.ready.map((x: any) => x.n), cube: s.cube.map((x: any) => x.n) };
      }
      const box = document.getElementById('rune-craftable') as HTMLElement;
      return {
        readyNames: status.ready,
        readyTitle: !!box.querySelector('.rw-make-group-title'),
        domHasInsight: /Insight/.test(box.innerHTML),
        domHasTreachery: /Treachery/.test(box.innerHTML),
      };
    });
    // Spirit (Tal+Thul+Ort+Amn), Insight (Ral+Tir+Tal+Sol), Treachery (Shael+Thul+Lem),
    // Lawbringer (Amn+Lem+Ko) are all fully in hand
    expect(r.readyNames).toContain('Insight');
    expect(r.readyNames).toContain('Treachery');
    expect(r.readyNames).toContain('Lawbringer');
    expect(r.readyNames.some((n: string) => /^Spirit/.test(n))).toBe(true);
    expect(r.readyTitle).toBe(true);
    expect(r.domHasInsight).toBe(true);
    expect(r.domHasTreachery).toBe(true);
  });

  test('importing a tally writes the counts to the stash and persists', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ta = document.getElementById('rune-import-box') as HTMLTextAreaElement;
      ta.value = 'Ist:3, Vex:1, el:2';   // mixed case + commas, lowercase normalised
      (window as any).importRuneTally();
      const saved = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}');
      const shownIst = (document.querySelector('.rs-count[data-rune-count="Ist"]') as HTMLElement).textContent!.trim();
      const status = (document.getElementById('rune-import-status') as HTMLElement).textContent || '';
      return { saved, shownIst, status, junk: (window as any).runewordReq({ runes: 'Zzz + Qqq' }) };
    });
    expect(r.saved.Ist).toBe(3);
    expect(r.saved.Vex).toBe(1);
    expect(r.saved.El).toBe(2);          // "el" normalised to El
    expect(r.shownIst).toBe('3');
    expect(r.status.toLowerCase()).toMatch(/loaded/);
    expect(r.junk).toBeNull();           // garbage rune names parse to nothing
  });

  test('no console errors across the craft + collapse + import flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="runes"]');
    await page.waitForTimeout(150);
    await page.click('#rune-stash-card .boss-header');
    await page.evaluate(() => {
      const ta = document.getElementById('rune-import-box') as HTMLTextAreaElement;
      ta.value = 'Tal:3 Sol:2 Ral:1 Tir:1';
      (window as any).importRuneTally();
      (window as any).renderRuneStash();
    });
    await page.waitForTimeout(120);
    expect(errors).toEqual([]);
  });
});
