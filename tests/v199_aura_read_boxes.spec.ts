// v199 — per-boss AURA READ quick-decision boxes (Konyo's ask: the visibility
// rules explained individually, visual and to the point, ON each ID card).
// Hephasto: NEVER blind (always Aura Enchanted) — fast attacks=Fana(kept),
// resists drop=Conviction(→Fana), chilled=HF, nothing=skip. Lister: the
// NAMEPLATE decides — AE listed = readable like Hephasto (minions flash the
// aura); NOT listed = the ONLY blind case (BD-20 grant at bind, ~1-in-5).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v199 aura-read boxes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
  });

  test('Hephasto card: NEVER-blind box with 2 win-rows (Fana kept, Conviction remap) + skip row', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Hephasto the Armorer');
      const box = document.querySelector('#bindsu-detail .aura-read') as HTMLElement;
      if (!box) return { box: false };
      const title = box.querySelector('.ar-title')!.textContent!;
      const wins = [...box.querySelectorAll('.ar-row.ar-win')].map(e => e.textContent!);
      return {
        box: true,
        neverBlind: title.includes('NEVER blind'),
        winCount: wins.length,
        fanaKept: wins.some(t => t.includes('Fanaticism') && t.includes('kept')),
        convRemap: wins.some(t => t.includes('Conviction') && t.includes('remaps to Fanaticism')),
        skipRow: !!box.querySelector('.ar-row.ar-skip'),
        noGates: !box.querySelector('.ar-gate'), // gates are Lister's nameplate logic only
      };
    });
    expect(r.box).toBe(true);
    expect(r.neverBlind).toBe(true);
    expect(r.winCount).toBe(2);
    expect(r.fanaKept).toBe(true);
    expect(r.convRemap).toBe(true);
    expect(r.skipRow).toBe(true);
    expect(r.noGates).toBe(true);
  });

  test('Lister card: NAMEPLATE-decides box with yes-gate, blind-gate, and the minion-animation tell', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Lister the Tormentor');
      const box = document.querySelector('#bindsu-detail .aura-read') as HTMLElement;
      if (!box) return { box: false };
      const txt = box.textContent!;
      return {
        box: true,
        nameplate: box.querySelector('.ar-title')!.textContent!.includes('NAMEPLATE decides'),
        yesGate: !!box.querySelector('.ar-gate.ar-yes'),
        blindGate: !!box.querySelector('.ar-gate.ar-blind'),
        minionTell: txt.includes('7 minions flash the aura animation'),
        onlyBlindCase: txt.includes('ONLY blind case') && txt.includes('never happen on Hephasto'),
        convRemap: txt.includes('remaps to Fanaticism'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });

  test('boxes render ABOVE the long-form disclaimer; other bind cards have no box', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Lister the Tormentor');
      const detail = document.getElementById('bindsu-detail')!;
      const html = detail.innerHTML;
      const order = html.indexOf('aura-read') < html.indexOf('AURA VISIBILITY');
      (window as any).openBindSUByName('The Smith');
      const smithBox = !!document.querySelector('#bindsu-detail .aura-read');
      return { order, smithBox };
    });
    expect(r.order).toBe(true);
    expect(r.smithBox).toBe(false);
  });
});
