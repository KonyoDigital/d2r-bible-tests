import { test, expect } from './_net_stub';
import * as path from 'path';

// v1748 — THE BUILD BADGE SAID THE VERSION TWICE.
//
// Found by the second eye, on the pixels: it reported the stamp rendering as `v1747 · 2026-08-17 ·
// v174…`. The truncation itself is v1691.1's deliberate design — the badge is capped at 180px so
// that "is this tab stale?" (id + date) always survives and the ship NAME is the decoration that
// clips. That part was working.
//
// The waste was underneath it: `D2R_BUILD.name` already BEGINS with the id ("v1747 - the tally
// search bar"), so the line composed `id · date · name` and printed the version twice — 319px of
// content in a 180px box, where every character surviving the ellipsis after the date was an echo
// of the id. Now 269px, and the visible remainder carries the name.
//
// Stripped at DISPLAY time only, in the badge and the tab title. `D2R_BUILD.name` is left exactly as
// it is, because other readers key on it — the meta tags, the console footer stamp, the version
// gates. Fixing the field would have been the wider blast radius for the same pixels.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1748 — the build stamp says the version once', () => {
  test('★★★ neither the badge nor the tab title repeats the version', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    const r = await page.evaluate(() => {
      const w: any = window;
      const el = document.getElementById('v687-build-badge');
      const B = w.D2R_BUILD || {};
      const txt = el ? (el.textContent || '') : '';
      const count = (s: string, needle: string) =>
        needle ? s.split(needle).length - 1 : 0;
      return {
        id: B.id, name: B.name, badge: txt, title: document.title,
        idInBadge: count(txt, String(B.id || '')),
        idInTitle: count(document.title, String(B.id || '')),
        // the fields the design guarantees survive the clip
        hasId: txt.indexOf(String(B.id || '')) === 0,
        hasDate: txt.indexOf(String(B.date || '')) > 0,
      };
    });
    expect(r.id, 'no build id to check').toBeTruthy();
    // non-vacuity: the name must actually still carry a version prefix upstream, or this test is
    // asserting against a problem that no longer exists and would pass for the wrong reason
    expect(String(r.name), 'D2R_BUILD.name no longer starts with the id — retire this gate')
      .toMatch(/^v\d/);
    expect(r.idInBadge, 'the badge prints the version twice: ' + r.badge).toBe(1);
    expect(r.idInTitle, 'the tab title prints the version twice: ' + r.title).toBe(1);
    // and v1691.1's guarantee is untouched — id first, date present
    expect(r.hasId, 'the badge no longer leads with the build id: ' + r.badge).toBe(true);
    expect(r.hasDate, 'the badge lost its date: ' + r.badge).toBe(true);
  });
});
