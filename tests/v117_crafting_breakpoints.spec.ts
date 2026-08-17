// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// Nightly bridges B3 + B4 — two additive reference-tab sections in the 📐 reference tab.
//   · B4 🔨 Crafted-item recipes — the 4 crafts keyed on their PERFECT GEM (the gem sets
//     the craft type; the rune varies by slot and doesn't change the result), the 3
//     guaranteed mods each, the ilvl formula, with a RotW affix-pool caveat.
//   · B3 ⚡ Breakpoints — the canonical vanilla Sorceress FCR + FHR frame tables (the
//     caster reference for a Warlock), with a strong RotW "verify your own frames" caveat.
// Additive only — nothing on the tab was removed; cube + merc + MF sections all remain.
test.describe('v117 crafting + breakpoints reference (nightly B3+B4)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  const refBodyText = async (page: any, re: RegExp) =>
    page.evaluate((src: string) => {
      const heads = Array.from(document.querySelectorAll('#tab-ref h2.sec-h')) as HTMLElement[];
      const h = heads.find((x) => new RegExp(src, 'i').test(x.textContent || ''));
      const body = h ? (h.nextElementSibling as HTMLElement) : null;
      return body ? (body.textContent || '') : '';
    }, re.source);

  test('the reference tab gains BOTH new sections, additively (cube + merc + MF still present)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ref = document.getElementById('tab-ref');
      const headers = ref ? Array.from(ref.querySelectorAll('h2.sec-h')).map((h) => h.textContent || '') : [];
      return {
        hasCraft: headers.some((t) => /Crafted-item recipes/i.test(t)),
        hasBp: headers.some((t) => /Breakpoints/i.test(t)),
        hasCube: headers.some((t) => /Cube Recipes/i.test(t)),
        hasMerc: headers.some((t) => /Mercenary mechanics/i.test(t)),
        hasMF: headers.some((t) => /MF math/i.test(t)),
      };
    });
    expect(r.hasCraft).toBe(true);
    expect(r.hasBp).toBe(true);
    expect(r.hasCube).toBe(true);
    expect(r.hasMerc).toBe(true);
    expect(r.hasMF).toBe(true);
  });

  test('B4 crafted recipes — the 4 crafts keyed on their perfect gem, with guaranteed mods + ilvl rule + RotW caveat', async ({ page }) => {
    const txt = await refBodyText(page, /Crafted-item recipes/);
    expect(txt).toContain('Perfect Amethyst');
    expect(txt).toContain('Perfect Ruby');
    expect(txt).toContain('Perfect Emerald');
    expect(txt).toContain('Perfect Sapphire');
    expect(txt).toContain('Caster');
    expect(txt).toContain('Faster Cast Rate');
    expect(txt).toMatch(/Life stolen/i);
    expect(txt).toMatch(/Frost Nova/i);
    // the gem (not the rune) defines the craft; rune varies by slot
    expect(txt).toMatch(/rune only varies by item slot/i);
    // ilvl formula
    expect(txt).toMatch(/0\.5 × clvl/);
    // RotW guard-rail + Warlock cross-ref
    expect(txt).toMatch(/Reign of the Warlock|RotW/i);
    expect(txt).toContain('Warlock');
    expect(txt).toContain('Breakpoints');
  });

  test('B3 breakpoints — Sorceress FCR + FHR tables correct, with the strong RotW caveat', async ({ page }) => {
    const txt = await refBodyText(page, /Breakpoints/);
    // FCR anchors (the two meta targets)
    expect(txt).toContain('Faster Cast Rate');
    expect(txt).toMatch(/63/);
    expect(txt).toMatch(/37/);
    expect(txt).toMatch(/105/);
    // FHR anchors
    expect(txt).toContain('Faster Hit Recovery');
    expect(txt).toMatch(/142/);
    expect(txt).toMatch(/280/);
    // mechanic + RotW caveat
    expect(txt).toMatch(/25 frames\/sec|25 frames|frames\/sec/i);
    expect(txt).toMatch(/Reign of the Warlock|RotW/i);
    expect(txt).toMatch(/Sorceress/i);
    // Warlock cross-ref to the crafted section
    expect(txt).toContain('Caster-crafted');
  });

  test('no console errors activating the reference tab + expanding the two new sections', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).switchTab('ref'));
    await page.waitForTimeout(120);
    await page.evaluate(() => {
      document.querySelectorAll('#tab-ref h2.sec-h').forEach((h) => {
        if (/Crafted-item recipes|Breakpoints/i.test(h.textContent || '')) (window as any).toggleSec(h);
      });
    });
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });
});
