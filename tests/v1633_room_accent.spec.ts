/* v1633 — THE COMPLETED SUBTAB WEARS ITS OWN ROOM'S COLOUR.
 *
 * Konyo, looking at Forge → Completed: "needs to be color synced this color for runewords right?
 * it looks a litle off compared to the updated tab color we picked".
 *
 * The item NAMES in that list were already right (a completed runeword's name is the same gold as
 * a unique — the game gives runewords no colour of their own). What was wrong is that every rule
 * for that panel is written `:is(#tab-forge,#tab-funi,#tab-fsets)` — ONE declaration painting
 * THREE rooms — with the rail and tick hardcoded to a green literal. The panel therefore rendered
 * byte-identical in all three tabs and carried the accent of none of them.
 *
 * WHY THIS SPEC CAN FAIL: it reads the SAME selector in all three rooms and requires three
 * different answers. A shared rule with a literal in it gives one answer three times and reds
 * here. No colour literal is written below — each room is compared to the token its own tab
 * claims, so correcting the palette can never red this file (the v1621 lesson in _palette.ts).
 */
import { test, expect } from '@playwright/test';
import * as path from 'path';
import { tokenRGB } from './_palette';

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* room id -> the token that room's TAB is painted with (v1631/v1633). */
const ROOMS = [
  { tab: 'forge', token: '--rune' },
  { tab: 'funi',  token: '--q-unique' },
  { tab: 'fsets', token: '--q-set' },
] as const;

test.describe('v1633 — the shared Forge-family chrome follows its room', () => {
  test('★★★ --room resolves to a DIFFERENT, tab-correct colour in each of the three rooms', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2400);

    const seen: string[] = [];
    for (const r of ROOMS) {
      const want = await tokenRGB(page, r.token);
      expect(want, `the board must declare ${r.token}`).toBeTruthy();

      // Resolve --room INSIDE the real tab element, through the cascade — not by parsing text.
      const got = await page.evaluate((tab: string) => {
        const host = document.querySelector('#tab-' + tab) as HTMLElement | null;
        if (!host) return { missing: true, color: null as string | null };
        const probe = document.createElement('span');
        probe.style.cssText = 'position:absolute;left:-9999px;top:-9999px';
        probe.style.color = 'rgb(1, 2, 3)';                 // impossible => "did not resolve"
        probe.style.setProperty('color', 'var(--room)');
        host.appendChild(probe);
        const c = getComputedStyle(probe).color;
        probe.remove();
        return { missing: false, color: c === 'rgb(1, 2, 3)' ? null : c };
      }, r.tab);

      expect(got.missing, `#tab-${r.tab} must exist to carry a room accent`).toBe(false);
      expect(got.color, `#tab-${r.tab} must declare --room (it resolved to nothing)`).not.toBeNull();
      expect(got.color, `#tab-${r.tab}'s --room must equal its tab token ${r.token}`).toBe(want);
      seen.push(got.color as string);
    }

    // The failure this exists to catch: one shared literal answering for all three rooms.
    expect(new Set(seen).size,
      `the three rooms must accent differently, got ${seen.join(' / ')}`).toBe(ROOMS.length);
  });

  test('★★★ the completed-row rail and tick are driven by --room, not a green literal', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2400);

    // Build the REAL markup the Forge renders for a completed row, inside each real tab, and read
    // what the shipped stylesheet paints it. Nothing is stubbed: the classes are the ones in
    // _doneList, so a rule that stops matching them fails here.
    const painted = await page.evaluate((tabs: string[]) => {
      const out: Record<string, { rail: string; tick: string } | null> = {};
      for (const tab of tabs) {
        const host = document.querySelector('#tab-' + tab) as HTMLElement | null;
        if (!host) { out[tab] = null; continue; }
        const row = document.createElement('div');
        row.className = 'f-donerow';
        row.innerHTML = '<span class="f-doneck">✓</span><span class="f-donename">Wrath</span>';
        host.appendChild(row);
        const tick = row.querySelector('.f-doneck') as HTMLElement;
        out[tab] = {
          rail: getComputedStyle(row).borderLeftColor,
          tick: getComputedStyle(tick).color,
        };
        row.remove();
      }
      return out;
    }, ROOMS.map(r => r.tab));

    for (const r of ROOMS) {
      const want = await tokenRGB(page, r.token);
      const got = painted[r.tab];
      expect(got, `no completed row could be rendered inside #tab-${r.tab}`).not.toBeNull();
      expect(got!.rail, `the completed-row rail in ${r.tab} must be its room colour`).toBe(want);
      expect(got!.tick, `the completed-row tick in ${r.tab} must be its room colour`).toBe(want);
    }

    // ...and all three must not collapse onto one another (the pre-v1633 state exactly).
    const rails = ROOMS.map(r => painted[r.tab]!.rail);
    expect(new Set(rails).size,
      `the completed rows must differ per room, got ${rails.join(' / ')}`).toBe(ROOMS.length);
  });
});
