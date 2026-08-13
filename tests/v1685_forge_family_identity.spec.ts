import { test, expect } from './_net_stub';
import * as path from 'path';

// v1685 — THE THREE FORGE PAGES WEAR ONE IDENTITY EACH, AND #tab-forge IS FINALLY MEASURED.
//
// Two things brought this file into existence, and the second is the reason the first survived
// three versions.
//
// 1. THE FORGE TITLE HAD NEVER TAKEN THE COLOUR v1672 SAID IT TOOK. v1672's message reads "THE
//    FORGE TITLE TAKES RUNEWORD GOLD", and the rule it added — `#tab-forge .forge-title{color:
//    var(--q-runeword)}` — really is in the file. It just never painted. The family rule
//    `:is(#tab-forge,#tab-funi,#tab-fsets) .forge-title{…color:#f0c060}` has the SAME specificity
//    (:is() takes its most specific argument, an id, so both are (1,1,0)) and is written LATER, so
//    source order won. Measured before the fix: rgb(240,192,96), chrome gold. #tab-funi and
//    #tab-fsets look correct only because their overrides happen to sit after that rule. v1685
//    moved the Forge rule down beside them; nothing about the rule itself changed.
//
// 2. NOBODY HAD EVER LOOKED. v1672 and v1678 both shipped saying, honestly, that the #tab-forge
//    header could not be render-verified because it is JS-built and "needs app data". It does not:
//    switchTab('forge') builds it, and then it measures like any other element. A gap stated in
//    two commit messages is still a gap, and it is exactly where the unpainted colour hid.
//
// So this asserts the RESOLVED colour of each of the three titles against the token it is supposed
// to wear — never against a literal, so retuning a token moves the page and the test together —
// and it asserts each header renders ITS OWN tab icon, decoded, which is the v1678 invariant.
//
// Forge and F·Uniques resolving to the SAME colour was v1672's call, and it stood until v1702
// surfaced that four specs disagreed. 2026-08-13 — KONYO RULED (bible.html:7924 ruling block):
// "these two colors cant be the same... RUNEWORD is separate from the F-UNIQUES" — an item NAME
// obeys the game, but A TAB IS A LABEL FOR A ROOM. The Forge room now wears its TAB's rune colour
// (--rune), same as F·Uniques wears --q-unique and F·Sets wears --q-set: three distinct rooms,
// three distinct identities. What must never happen is any of them falling back to chrome gold,
// which is what this catches.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const FAMILY = [
  { tab: 'forge', title: 'Forge', token: '--rune', icon: 'ui_tab_forge.png' },
  { tab: 'funi', title: 'Forge · Uniques', token: '--q-unique', icon: 'ui_tab_funi.png' },
  { tab: 'fsets', title: 'Forge · Sets', token: '--q-set', icon: 'ui_tab_fsets.png' },
];

test.describe('v1685 — the Forge family identity', () => {
  for (const f of FAMILY) {
    test(`★★★ ${f.tab}: the title wears ${f.token} and the header wears ${f.icon}`, async ({ page }) => {
      await page.goto(URL, { waitUntil: 'load' });
      await page.waitForFunction(() => typeof (window as any).switchTab === 'function', null, { timeout: 20000 });
      // #tab-forge is JS-built — this is the step v1672/v1678 assumed was impossible
      await page.evaluate((t) => { try { (window as any).switchTab(t); } catch (e) { /* already there */ } }, f.tab);
      await page.waitForFunction((t) => !!document.querySelector('#tab-' + t + ' .forge-title'),
                                f.tab, { timeout: 10000 });
      const r = await page.evaluate(({ tab, token }) => {
        const el = document.querySelector('#tab-' + tab + ' .forge-title');
        const img = document.querySelector('#tab-' + tab + ' .tvf-emblem img') as HTMLImageElement | null;
        // resolve the token through the browser so the test never hard-codes a hex
        const probe = document.createElement('span');
        probe.style.color = 'var(' + token + ')';
        document.body.appendChild(probe);
        const want = getComputedStyle(probe).color;
        probe.style.color = 'var(--gold-bright)';
        const chrome = getComputedStyle(probe).color;
        probe.remove();
        return {
          text: el ? (el.textContent || '').trim() : null,
          color: el ? getComputedStyle(el).color : null,
          want, chrome,
          src: img ? (img.currentSrc || img.src).split('/').pop()!.split('?')[0] : null,
          decoded: img ? img.naturalWidth : 0,
        };
      }, { tab: f.tab, token: f.token });

      expect(r.text, `#tab-${f.tab} rendered no page title`).toBe(f.title);
      expect(r.color, `the ${f.tab} title is not wearing ${f.token}`).toBe(r.want);
      /* the specific way it broke: an override that loses to the family rule leaves chrome gold.
         Skipped where the token IS chrome gold, so this can never be vacuously true. */
      if (r.want !== r.chrome) {
        expect(r.color, `the ${f.tab} title fell back to chrome gold — its override lost to `
                      + ':is(#tab-forge,#tab-funi,#tab-fsets) .forge-title. LAST RULE WINS: move it below that rule.')
          .not.toBe(r.chrome);
      }
      // v1678 — a tab and its page header show the same picture, and it actually decodes
      expect(r.src, `the ${f.tab} header is not on its own tab icon`).toBe(f.icon);
      expect(r.decoded, `${f.icon} did not decode in the ${f.tab} header`).toBeGreaterThan(0);
    });
  }

  test('★★★ the three titles are told apart — each room its own colour (2026-08-13 ruling)', async ({ page }) => {
    /* NON-VACUITY: after his ruling, Forge/F·Uniques/F·Sets each wear a DIFFERENT token
       (--rune / --q-unique / --q-set), so all three should now resolve to distinct colours. */
    await page.goto(URL, { waitUntil: 'load' });
    await page.waitForFunction(() => typeof (window as any).switchTab === 'function', null, { timeout: 20000 });
    const seen: string[] = [];
    for (const f of ['forge', 'funi', 'fsets']) {
      await page.evaluate((t) => { try { (window as any).switchTab(t); } catch (e) { /* noop */ } }, f);
      await page.waitForFunction((t) => !!document.querySelector('#tab-' + t + ' .forge-title'), f, { timeout: 10000 });
      seen.push(await page.evaluate((t) =>
        getComputedStyle(document.querySelector('#tab-' + t + ' .forge-title')!).color, f));
    }
    expect(seen[2], 'Forge · Sets is not distinct from Forge — the set green is gone')
      .not.toBe(seen[0]);
    expect(seen[1], 'Forge · Uniques is not distinct from Forge — the rune colour is gone')
      .not.toBe(seen[0]);
    expect(new Set(seen).size, `the three titles resolved ${new Set(seen).size} distinct colours, expected 3`)
      .toBe(3);
  });
});
