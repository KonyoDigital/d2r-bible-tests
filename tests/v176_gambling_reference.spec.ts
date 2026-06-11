import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v176 — Bridge B2 of the nightly maxroll gap-map: the reference tab gains a
// Gambling section (#gambling-ref). Gambling is the one drop source Magic Find
// can't touch, and it was previously 0% covered. All numbers are VERIFIED — the
// fixed quality odds (1797/200/2/1 per 2000), the per-act NPCs, ilvl=clvl, the
// rings/amulets-always-in-window + MF-irrelevance rules — sourced from maxroll's
// Gambling resource + fextralife's D2R gamble odds. The "dream uniques" list is
// flagged as vanilla examples to confirm in Reign of the Warlock (no fabricated
// RotW-specific claims). Additive only — slots into the existing sec-h/sec-body
// reference accordion right after Mercenary mechanics.

test.describe('v176 Gambling reference section (Bridge B2)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(900);
  });

  test('the Gambling section exists in the reference accordion and toggles open', async ({ page }) => {
    const r = await page.evaluate(() => {
      const body = document.getElementById('gambling-ref');
      const head = body ? (body.previousElementSibling as HTMLElement) : null;
      const isSecHead = !!head && head.classList.contains('sec-h');
      const title = head ? (head.querySelector('.sec-h-t')?.textContent || '').trim() : '';
      const startsHidden = body ? body.hasAttribute('hidden') : null;
      // open it via the real toggle handler
      if (head) head.click();
      const openAfter = body ? !body.hasAttribute('hidden') : null;
      return { hasBody: !!body, isSecHead, title, startsHidden, openAfter };
    });
    expect(r.hasBody).toBe(true);
    expect(r.isSecHead).toBe(true);
    expect(r.title).toBe('Gambling');
    expect(r.startsHidden).toBe(true);   // collapsed by default like every other ref section
    expect(r.openAfter).toBe(true);      // toggleSec opens it
  });

  test('the verified fixed quality odds are present (1797/200/2/1 per 2000)', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('gambling-ref')?.textContent || '').replace(/\s+/g, ' '));
    expect(txt).toContain('89.85%');
    expect(txt).toContain('1797 / 2000');
    expect(txt).toContain('200 / 2000');   // Rare 10%
    expect(txt).toContain('2 / 2000');     // Set 0.10%
    expect(txt).toContain('1 / 2000');     // Unique 0.05%
    expect(txt).toContain('0.05%');
  });

  test('all five per-act gambling NPCs are listed', async ({ page }) => {
    const txt = await page.evaluate(() => document.getElementById('gambling-ref')?.textContent || '');
    for (const npc of ['Gheed', 'Elzix', 'Alkor', 'Jamella', 'Anya']) {
      expect(txt, `${npc} listed`).toContain(npc);
    }
  });

  test('the honest mechanics rules are stated (MF-irrelevant, ilvl=clvl, RotW caveat)', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('gambling-ref')?.textContent || '').replace(/\s+/g, ' '));
    expect(txt).toMatch(/Magic Find does NOT touch|Magic Find does nothing/i);
    expect(txt).toMatch(/Item level = your character level/i);
    expect(txt).toMatch(/Reign of the Warlock/i);     // RotW guard-rail present, no fabricated odds
    expect(txt).toMatch(/Stone of Jordan/);           // the named ring target
  });

  test('no console errors opening the gambling section', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      const head = document.getElementById('gambling-ref')?.previousElementSibling as HTMLElement;
      head && head.click();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
