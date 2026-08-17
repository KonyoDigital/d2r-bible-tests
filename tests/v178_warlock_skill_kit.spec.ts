// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v178 — Bridge B5 of the nightly maxroll gap-map: the reference tab gains a
// "Warlock skill kit" overview (#warlock-skill-kit). The bible covered Bind Demon
// mechanics exhaustively (binds tab) but never laid out the build's ACTIVE skill
// kit — it assumed you already knew what Echoing Strike is. This section closes
// that gap with VERIFIED Reign-of-the-Warlock S14 mechanics sourced from maxroll's
// Echoing Strike Warlock guide + icy-veins' skill page (Echoing Strike spawns up to
// 5 weapon echoes off FCR; Mirrored Blades / Blade Warp / Hex Bane synergies;
// Demonic Mastery 10pt→2 Defilers; Consume; 125% FCR target). Additive only — slots
// into the existing sec-h/sec-body reference accordion just before the Warlock bind
// sources section, with a RotW "verify live tooltips" caveat (no fabricated numbers).

test.describe('v178 Warlock skill kit reference (Bridge B5)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(800);
  });

  test('the section exists in the reference accordion and toggles open', async ({ page }) => {
    const r = await page.evaluate(() => {
      const body = document.getElementById('warlock-skill-kit');
      const head = body ? (body.previousElementSibling as HTMLElement) : null;
      const isSecHead = !!head && head.classList.contains('sec-h');
      const title = head ? (head.querySelector('.sec-h-t')?.textContent || '').trim() : '';
      const startsHidden = body ? body.hasAttribute('hidden') : null;
      if (head) head.click();
      const openAfter = body ? !body.hasAttribute('hidden') : null;
      return { hasBody: !!body, isSecHead, title, startsHidden, openAfter };
    });
    expect(r.hasBody).toBe(true);
    expect(r.isSecHead).toBe(true);
    expect(r.title).toBe('Warlock skill kit');
    expect(r.startsHidden).toBe(true);
    expect(r.openAfter).toBe(true);
  });

  test('the verified Echoing Strike mechanic is stated (up to 5 echoes off FCR)', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('warlock-skill-kit')?.textContent || '').replace(/\s+/g, ' '));
    expect(txt).toContain('Echoing Strike');
    expect(txt).toMatch(/up to 5 echoes/i);
    expect(txt).toMatch(/Faster Cast Rate/i);
    expect(txt).toMatch(/base damage \+ Enhanced Damage/i);
  });

  test('the core synergies + summon/consume kit are present', async ({ page }) => {
    const txt = await page.evaluate(() => document.getElementById('warlock-skill-kit')?.textContent || '');
    for (const skill of ['Mirrored Blades', 'Blade Warp', 'Hex Bane', 'Levitation Mastery', 'Demonic Mastery', 'Consume', 'Bind Demon']) {
      expect(txt, `${skill} listed`).toContain(skill);
    }
    expect(txt).toMatch(/10 points/i);          // Demonic Mastery summon point
    expect(txt).toMatch(/Summon Defiler/i);      // consume target
    expect(txt).toMatch(/125% Faster Cast Rate|125% FCR/i); // breakpoint target
  });

  test('the RotW caveat + source cite are present (no fabricated numbers)', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('warlock-skill-kit')?.textContent || '').replace(/\s+/g, ' '));
    expect(txt).toMatch(/Reign-of-the-Warlock|Reign of the Warlock/i);
    expect(txt).toMatch(/verify the live tooltips in-game/i);
    expect(txt).toMatch(/maxroll\.gg/i);
    expect(txt).toMatch(/icy-veins/i);
  });

  test('the Bind Demon row cross-links to the binds tab', async ({ page }) => {
    const ok = await page.evaluate(() => {
      const body = document.getElementById('warlock-skill-kit');
      const link = body ? Array.from(body.querySelectorAll('[onclick]')).find((e) => /switchTab\('binds'\)/.test(e.getAttribute('onclick') || '')) : null;
      return !!link;
    });
    expect(ok).toBe(true);
  });

  test('no console errors opening the section', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      const head = document.getElementById('warlock-skill-kit')?.previousElementSibling as HTMLElement;
      head && head.click();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
