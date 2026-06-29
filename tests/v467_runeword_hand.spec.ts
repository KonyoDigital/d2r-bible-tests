// v467 — 1H vs 2H badge on weapon runewords (Konyo: knowing the hand is crucial). _rwHand derives it from the
// runeword's base-type string: missile/polearm/spear/staff = 2H; scepter/wand/mace/dagger/katar = 1H;
// sword/axe/hammer/(generic|melee) Weapons = 1H/2H; armor/shield = none.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v467 runeword 1H/2H hand', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any)._rwHand);
  });

  test('_rwHand classifies base-type strings correctly', async ({ page }) => {
    const r = await page.evaluate(() => {
      const h = (window as any)._rwHand;
      return {
        polearmsSpears: h('4 socket Polearms Spears'),       // 2H
        missile: h('4 socket Missile Weapons'),               // 2H
        insight: h('4 socket Polearms Staves Missile Weapons'),// 2H (the "weapons" must not fake 1H/2H)
        scepter: h('4 socket Scepters'),                      // 1H
        daggers: h('3 socket Daggers'),                       // 1H
        katars: h('3 socket Katars'),                         // 1H
        swordsAxes: h('5 socket Swords Axes'),                // 1H/2H
        genericWeapons: h('6 socket Weapons'),                // 1H/2H
        meleeWeapons: h('5 socket Melee Weapons'),            // 1H/2H
        macesStaves: h('4 socket Maces Staves Scepters'),     // 1H/2H (mace/scepter 1H + staff 2H)
        bodyArmor: h('4 socket Body Armor'),                  // none
        helms: h('3 socket Helms'),                           // none
        shields: h('3 socket Shields'),                       // none
      };
    });
    expect(r.polearmsSpears).toBe('2H');
    expect(r.missile).toBe('2H');
    expect(r.insight).toBe('2H');
    expect(r.scepter).toBe('1H');
    expect(r.daggers).toBe('1H');
    expect(r.katars).toBe('1H');
    expect(r.swordsAxes).toBe('1H/2H');
    expect(r.genericWeapons).toBe('1H/2H');
    expect(r.meleeWeapons).toBe('1H/2H');
    expect(r.macesStaves).toBe('1H/2H');
    expect(r.bodyArmor).toBe('');
    expect(r.helms).toBe('');
    expect(r.shields).toBe('');
  });

  test('the Chronicle row shows the hand badge for a weapon runeword', async ({ page }) => {
    await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
    await page.waitForTimeout(800);
    const html = await page.evaluate(() => {
      const w = window as any;
      const c = document.getElementById('rw-chronicle-card'); if (c) c.classList.remove('collapsed');
      w.rwcSetFilter && w.rwcSetFilter('all');
      w.renderRunewordChronicle && w.renderRunewordChronicle();
      return (document.getElementById('rwc-list') || {}).innerHTML || '';
    });
    expect(html).toContain('rwc-hand');           // the badge class is rendered
    expect(html).toMatch(/>1H<|>2H<|>1H\/2H</);   // at least one hand value shown
  });
});
