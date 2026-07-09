import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v633 — HOVER DEPTH PARITY (Konyo: "some are PERFECT and some are just plain picture with no
// detail — fix that across the platform"): every BASE_DB name resolves a RICH card (tier · sockets
// · reqs · its runewords), not a naked picture. The curated RW_BASES cards stay curated.

test('Scourge / War Spike / Ettin Axe / Executioner Sword — the exact bases from his screenshots hover RICH', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const probe = (n: string) => { const x = w._arttipResolve(n); return { rich: !!x.rich, base: /Base Item/.test(x.desc || ''), rws: /runewords on this base/i.test(x.desc || ''), sock: /socket/i.test(x.desc || '') }; };
    return { scourge: probe('Scourge'), warSpike: probe('War Spike'), ettin: probe('Ettin Axe'), exec: probe('Executioner Sword'),
             curatedStill: (() => { const x = w._arttipResolve('Berserker Axe'); return !!x.rich && /fastest elite axe/i.test(x.desc || ''); })() };
  });
  ['scourge','warSpike','ettin','exec'].forEach((k) => {
    expect((r as any)[k].rich).toBe(true);
    expect((r as any)[k].base).toBe(true);
    expect((r as any)[k].rws).toBe(true);
    expect((r as any)[k].sock).toBe(true);
  });
  expect(r.curatedStill).toBe(true);   // hand-curated cards keep their editorial notes
});

test('FULL SWEEP: all 500+ BASE_DB names resolve rich — zero plain-picture bases left anywhere', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const names = Object.keys(w.BASE_DB || {});
    const plain = names.filter((n) => { try { const x = w._arttipResolve(n); return !x.rich || !x.desc; } catch (e) { return true; } });
    return { total: names.length, plain: plain.slice(0, 20), plainCount: plain.length };
  });
  expect(r.total).toBeGreaterThan(400);
  expect(r.plainCount).toBe(0);
});
