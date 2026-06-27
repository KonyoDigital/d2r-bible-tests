import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v450 (CORRECTS v412) — a SUPERIOR base IS a normal-quality (white) item: it DOES form runewords like any
// white base and keeps its superior bonus on top. So:
//  • the base card shows the runeword "keep" guidance + a positive superior note (NOT "cannot make a runeword")
//  • a Superior socketed/Larzuk base registers as its OWN tile ("Superior <Base> …"), distinct from the white
//    one, so two physical items (one superior + one normal) no longer collapse into a single entry
//  • the "Superior " prefix is stripped for art / tier / socket-max lookups (so the tile still shows the base's
//    own art and exact max sockets), while the registered NAME keeps "Superior" as its display identity.

test('_qualStrip strips a leading quality word, keeps the bare base', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      sup: w._qualStrip('Superior Berserker Axe'),
      supSuffix: w._qualStrip('Superior Monarch (Larzuk base)'),
      plain: w._qualStrip('Berserker Axe'),
      low: w._qualStrip('Cracked Phase Blade'),
    };
  });
  expect(r.sup).toBe('Berserker Axe');
  expect(r.supSuffix).toBe('Monarch (Larzuk base)');
  expect(r.plain).toBe('Berserker Axe');     // no prefix → unchanged
  expect(r.low).toBe('Phase Blade');
});

test('Superior base resolves its bare base for tier + max sockets', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      tier: w._baseTier('Superior Berserker Axe'),
      maxSup: w._socketMaxFor('Superior Berserker Axe'),
      maxPlain: w._socketMaxFor('Berserker Axe'),
      monarch: w._socketMaxFor('Superior Monarch'),
    };
  });
  expect(r.tier).toBe('elite');
  expect(r.maxSup).toBe(6);          // prefix stripped → Berserker Axe = 6
  expect(r.maxPlain).toBe(6);
  expect(r.monarch).toBe(4);
});

test('a Superior base SHOWS runeword guidance + positive note (no "cannot" warning)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    // forceSuperior=true → the positive note fires even when the name itself isn't flagged
    const line = w._baseRWLine('Berserker Axe', 0, true);
    return { line };
  });
  expect(r.line).toContain('valid runeword base');
  expect(r.line).toContain('Keep for runewords');     // guidance is NOT suppressed
  expect(r.line.toLowerCase()).not.toContain('cannot make a runeword');
});

test('Superior socketed-base entry registers distinctly + carries the right note', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    const supName = 'Superior Berserker Axe (Larzuk base)';
    const plainName = 'Berserker Axe (Larzuk base)';
    w._ensureSocketBaseEntry(supName);
    w._ensureSocketBaseEntry(plainName);
    const sup = w.EXTRA_ITEMS[supName];
    const plain = w.EXTRA_ITEMS[plainName];
    return {
      distinct: supName !== plainName,
      supExists: !!sup,
      plainExists: !!plain,
      supBase: sup && sup.base,                 // bare base for art/lookups
      plainBase: plain && plain.base,
      supDesc: (sup && sup.desc) || '',
    };
  });
  expect(r.distinct).toBe(true);
  expect(r.supExists).toBe(true);
  expect(r.plainExists).toBe(true);
  expect(r.supBase).toBe('Berserker Axe');      // "Superior " stripped for art/lookups
  expect(r.plainBase).toBe('Berserker Axe');
  expect(r.supDesc).toContain('valid runeword base');
  expect(r.supDesc.toLowerCase()).not.toContain('cannot make a runeword');
});
