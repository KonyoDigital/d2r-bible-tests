import { test, expect } from './_net_stub';
import * as path from 'path';

// v1751 — A RUNEWORD SPELLED FOR A HUMAN MUST STILL FIND ITS BASES.
//
// Konyo, on this exact class: "i dont want random sockets numvers matching i need the baseitem
// releated to the specific and relvant runeword also matched! i wasted runewords" — and, after the
// Crescent Moon fix, "again check others for this exactly.. i want it accruate allround".
//
// Checking others for this exactly is what found it. RUNEWORDS carries 101 rows; RUNEWORD_TIP holds
// 99 keys and NOT ONE of them has a parenthesis. Six roster rows matched nothing:
//
//     Spirit (sword) · Spirit (shield) · Call to Arms (CTA) ·
//     Heart of the Oak (HotO) · Breath of the Dying (BotD) · Death's Web
//
// The first five are among the most-made runewords in the game, and every one of them rendered NO
// base at all: _forgeMetaBase returned [], so _rwHostBaseTiles hit `if (!names.length) return ''`
// and emitted an empty string. _baseRunewords speaks canonical names too, so even a populated meta
// list would have been thrown out by the class filter one line later — both ends broken by one
// cause, which is why one resolution fixes both.
//
// WHAT MAKES IT NASTY, and why it survived: _rwSock never had the bug. It read 4/5/4/6 correctly for
// all five. So the card showed a right socket count beside an empty base list — a half-answered card
// that reads like a gap in the data rather than a broken lookup. [[label-outlived-referent]]
//
// TWO THINGS MUST BOTH HOLD, and the second is why a naive strip would have been WORSE than the bug:
// RUNEWORD_TIP['Spirit'].b is "4 socket Swords or Shields", so the bare name returns the UNION.
// Strip-and-stop would offer a SWORD for "Spirit (shield)" — the precise defect he reported,
// arriving through its own fix. The parenthetical is data, not decoration.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const SPLIT = 'Spirit (shield)';
const ABBREV = ['Call to Arms (CTA)', 'Heart of the Oak (HotO)', 'Breath of the Dying (BotD)'];

async function board(page: any) {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any)._rwLegalBases === 'function'
    && typeof (window as any)._rwCanon === 'function', null, { timeout: 20000 });
  await page.waitForTimeout(1800);
}

test.describe('v1751 — display names resolve to their runeword', () => {
  test('★★★ every roster runeword offers at least one base — none render blank', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const rows = (w.RUNEWORDS || []).map((x: any) => x.n);
      const empty = rows.filter((n: string) => {
        // Death's Web is in the table as a UNIQUE for reference, not a runeword. It says so itself.
        const e = (w.RUNEWORDS || []).find((x: any) => x.n === n) || {};
        if (/not RW/i.test(String(e.runes || ''))) return false;
        return ((w._rwLegalBases(n) || []).length === 0);
      });
      return { total: rows.length, empty };
    });
    // non-vacuity: the roster must actually have been read
    expect(r.total, 'the runeword roster came back empty').toBeGreaterThan(90);
    expect(r.empty, 'runewords that offer NO base at all: ' + r.empty.join(', ')).toEqual([]);
  });

  test('★★★ the Spirit split stays split — a shield row never offers a sword', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const cats = (b: string) => (w._baseCats ? w._baseCats(b) || {} : {});
      const of = (n: string) => (w._rwLegalBases(n) || []).map((x: any) => (typeof x === 'string' ? x : x.n));
      const sh = of('Spirit (shield)'), sw = of('Spirit (sword)');
      return {
        shields: sh, swords: sw,
        shieldsThatAreNotShields: sh.filter((b: string) => !cats(b)['shield']),
        swordsThatAreNotSwords: sw.filter((b: string) => !cats(b)['sword']),
        // the union the bare name returns — proof the two rows are NOT just the same list twice
        identical: JSON.stringify(sh) === JSON.stringify(sw),
      };
    });
    expect(r.shields.length, 'Spirit (shield) offers nothing').toBeGreaterThan(0);
    expect(r.swords.length, 'Spirit (sword) offers nothing').toBeGreaterThan(0);
    expect(r.shieldsThatAreNotShields,
      'Spirit (shield) offered a non-shield: ' + r.shieldsThatAreNotShields.join(', ')).toEqual([]);
    expect(r.swordsThatAreNotSwords,
      'Spirit (sword) offered a non-sword: ' + r.swordsThatAreNotSwords.join(', ')).toEqual([]);
    expect(r.identical, 'both Spirit rows returned the SAME list — the variant filter is not running')
      .toBe(false);
  });

  test('★★★ the shopping-list tiles actually render for them, not an empty string', async ({ page }) => {
    await board(page);
    const r = await page.evaluate((names: string[]) => {
      const w: any = window;
      const out: any = {};
      names.forEach((n) => {
        let html = '';
        try { html = w._rwHostBaseTiles ? (w._rwHostBaseTiles(n) || '') : 'NOFN'; } catch (e) { html = 'ERR'; }
        out[n] = html.length;
      });
      // and the one that must STAY empty
      let dw = '';
      try { dw = w._rwHostBaseTiles ? (w._rwHostBaseTiles("Death's Web") || '') : ''; } catch (e) {}
      out.__deathsWeb = dw.length;
      return out;
    }, [SPLIT, ...ABBREV]);
    [SPLIT, ...ABBREV].forEach((n) => {
      expect(r[n], n + ' rendered an EMPTY base card (' + r[n] + ' chars)').toBeGreaterThan(200);
    });
    // Death's Web is a unique listed for reference. Rendering bases for it would be fabrication.
    expect(r.__deathsWeb, "Death's Web is not a runeword and must render no bases").toBe(0);
  });

  test('★★ the canonicaliser never strips a suffix it cannot justify', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const c = w._rwCanon;
      return {
        split: c('Spirit (shield)'),
        abbrev: c('Call to Arms (CTA)'),
        plain: c('Enigma'),
        notARuneword: c("Death's Web"),
        // a parenthetical whose bare name is NOT a known runeword must survive untouched
        invented: c('Totally Made Up (sword)'),
      };
    });
    expect(r.split.key, 'the split row did not resolve').toBe('Spirit');
    expect(r.split.cat, 'the item-class tag was dropped, so the variant filter cannot run').toBe('shield');
    expect(r.abbrev.key, 'the abbreviation row did not resolve').toBe('Call to Arms');
    // "CTA" names no item class, so it must NOT become a filter
    expect(r.abbrev.cat, 'an abbreviation was treated as an item class').toBe('');
    expect(r.plain.key, 'a plain name was altered').toBe('Enigma');
    expect(r.notARuneword.key, "Death's Web must not be rewritten").toBe("Death's Web");
    expect(r.invented.key, 'a suffix was stripped off a name that is not a runeword').toBe('Totally Made Up (sword)');
  });
});
