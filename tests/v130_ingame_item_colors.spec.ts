import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import { boardTokens, assertTokens } from './_palette';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1632 test-quality audit — shape 1 (hardcoded value duplicating an app constant).
   This file used to open with three module-level colour literals — GOLD, GREEN and ORANGE — each
   with a comment naming the very token it had copied (--q-unique, --q-set, --q-orange).
   Every one of them RESTATED a value the app owns, and two had already drifted off it:
     · --q-set is D2's game-extracted FontColorGreen, a hair darker than the fully saturated green
       the constant had frozen -> the spec went RED ON CORRECT CODE (the v1621 shape).
     · q-rune renders var(--rune), its OWN orange, NOT the crafted --q-orange -> with one shared
       ORANGE constant the spec was structurally unable to tell those two oranges apart.
   The board owns the values, so the test READS them and asserts RELATIONSHIPS:
   colour == its own token, and the qualities on this page stay mutually DISTINCT. */

/* Token keys read live off bible.html's :root via tests/_palette (P0):
   unique -> --q-unique · set -> --q-set · orange -> --q-orange (crafted) · rune -> --rune.
   No quality hex appears in this file, in code or in prose, by design. */
const KEYS = ['unique', 'set', 'orange', 'rune'] as const;

async function openAll(page: Page) {
  await page.evaluate(() => {
    document.querySelectorAll('details.all-drops-details').forEach((d) => d.setAttribute('open', ''));
  });
}
const nameCell = (page: Page, boss: string, item: string) =>
  page.locator(`#${boss} tr[data-item="${item}"] td.item-name`);

/** The one cell this page renders for each quality under audit. */
const SAMPLE: Record<'unique' | 'set' | 'rune' | 'orange', [string, string]> = {
  unique: ['mephisto', 'Harlequin Crest (Shako)'],
  set: ['mephisto', 'Tal Rasha set (any piece)'],
  rune: ['countess', 'Ist rune'],
  orange: ['summoner', 'Key of Hate'],
};

test.describe('v130 in-game item-quality name colors + Cinzel font', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(300);
    await openAll(page);
  });

  test('unique items render gold (incl. tricky names that are NOT materials)', async ({ page }) => {
    const t = await boardTokens(page);
    assertTokens(t, ...KEYS);
    for (const [boss, item] of [
      ['mephisto', 'Harlequin Crest (Shako)'],
      ['mephisto', 'The Stone of Jordan'],
      ['countess', 'Nokozan Relic'],
    ] as const) {
      const c = nameCell(page, boss, item);
      await expect(c).toHaveClass(/q-unique/);
      // == the token the board declares for unique, whatever the palette says today.
      await expect(c).toHaveCSS('color', t.unique);
    }
  });

  test('set items render the set token — not the unique gold', async ({ page }) => {
    const t = await boardTokens(page);
    assertTokens(t, ...KEYS);
    const c = nameCell(page, ...SAMPLE.set);
    await expect(c).toHaveClass(/q-set/);
    await expect(c).toHaveCSS('color', t.set);
    // v1622-class guard: a rarity class present but painted with someone else's colour.
    expect(t.set, 'set green must not collapse into unique gold').not.toBe(t.unique);
  });

  test('runes render the rune token — their OWN orange, not the crafted orange', async ({ page }) => {
    const t = await boardTokens(page);
    assertTokens(t, ...KEYS);
    const c = nameCell(page, ...SAMPLE.rune);
    await expect(c).toHaveClass(/q-rune/);
    // table.drops td.item-name.q-rune{color:var(--rune)} — a DIFFERENT orange from --q-orange.
    await expect(c).toHaveCSS('color', t.rune);
    expect(t.rune, 'rune orange must stay distinct from crafted orange').not.toBe(t.orange);
  });

  test('event tokens / shards render the crafted-orange token (q-material and q-crafted agree)', async ({ page }) => {
    const t = await boardTokens(page);
    assertTokens(t, ...KEYS);
    const c = nameCell(page, ...SAMPLE.orange);
    // v342: quest/event items (keys, organs, essences, Token, Worldstone Shard) classify into the
    // crafted-orange bucket in _artRarity — q-material and q-crafted share ONE token, --q-orange.
    await expect(c).toHaveClass(/q-(material|crafted)/);
    await expect(c).toHaveCSS('color', t.orange);

    // The intent is "both classes map to the SAME token", so assert it across every such cell
    // the app actually rendered, rather than trusting one sample.
    const scan = await page.evaluate(() => {
      const q = (sel: string) => Array.from(document.querySelectorAll(sel)) as HTMLElement[];
      const material = q('table.drops td.item-name.q-material');
      const crafted = q('table.drops td.item-name.q-crafted');
      const colours = [...material, ...crafted].map((el) => getComputedStyle(el).color);
      return { material: material.length, crafted: crafted.length, distinct: Array.from(new Set(colours)) };
    });
    expect(scan.material + scan.crafted, 'no q-material/q-crafted cells rendered — assertion would be vacuous').toBeGreaterThan(0);
    expect(scan.distinct, 'q-material and q-crafted must resolve to one and the same colour').toEqual([t.orange]);
  });

  test('the qualities on this page render four DISTINCT colours (no palette collapse)', async ({ page }) => {
    const t = await boardTokens(page);
    assertTokens(t, ...KEYS);
    const painted: Record<string, string> = {};
    for (const [quality, [boss, item]] of Object.entries(SAMPLE)) {
      const cell = nameCell(page, boss, item);
      await expect(cell, `${quality} sample cell must exist`).toHaveCount(1);
      painted[quality] = await cell.evaluate((el) => getComputedStyle(el).color);
    }
    // Four assertions of "== my own token" can all be green while the palette has collapsed
    // into one colour. This is the assertion that cannot.
    expect(new Set(Object.values(painted)).size, `qualities collapsed: ${JSON.stringify(painted)}`).toBe(4);
    // And each painted colour is still the token the board declares for it.
    expect(painted).toEqual({
      unique: t.unique,
      set: t.set,
      rune: t.rune,
      orange: t.orange,
    });
  });

  test('item names use the in-game-style Cinzel display serif', async ({ page }) => {
    const c = nameCell(page, 'mephisto', 'Harlequin Crest (Shako)');
    await expect(c).toHaveCSS('font-family', /Cinzel/i);
  });

  test('grail rarity is still signalled — the tier pill survives next to the name', async ({ page }) => {
    const row = page.locator('#mephisto tr[data-item="The Stone of Jordan"]');
    // SoJ is a grail-tier item — tierPill still renders <span class="pill pill-grail"> in the name cell
    await expect(row.locator('td.item-name span.pill-grail')).toHaveCount(1);
  });
});
