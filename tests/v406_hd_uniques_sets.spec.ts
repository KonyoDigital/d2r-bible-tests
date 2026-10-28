import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v406 put every spawnable unique/set item on its in-game BASE sprite (art/hd_*.png). #111 (REG-2805), his ruling
// 2026-10-28 (b): each unique shows ITS OWN picture on every surface. window._keeperArt answers, in this order: its own
// sprite from the game files (v384: The Gnasher, The Minotaur, Witchwild String), its own icon (mr_: Death's Web,
// Stormshield, Skin of the Vipermagi - the base sprite in the unique's own colour), and its base sprite only as the
// stated fallback (Goldstrike Arch and these set pieces have no picture of their own in the repo). NOT "Sander's Folly"
// - that's the set NAME aggregate, not an item, so it keeps its set art. The node law is
// tv/test_a_unique_wears_its_own_picture_everywhere.py; this drives the same answers in Chrome.
test.describe('v406 + REG-2805 art for uniques + sets', () => {
  test('each item resolves to its own picture, and to its base sprite only when it has none', async ({ page }) => {
    const errs:string[]=[];
    page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
    page.on('pageerror',e=>errs.push(e.message));
    await page.goto(URL); await page.waitForTimeout(1500);
    const r = await page.evaluate(() => {
      const w:any = window;
      const names = ["The Gnasher","Goldstrike Arch","Death's Web","Tal Rasha's Guardianship",
                     "Sander's Paragon","Aldur's Rhythm","The Minotaur",
                     "Witchwild String","Stormshield","Skin of the Vipermagi","Civerb's Ward"];
      const out:any = {};
      for (const n of names){
        try { const k = w._keeperArt(n); out[n] = [w.artUrl(n), k && k.url, k && k.from]; } catch(e){ out[n] = ['ERR']; }
      }
      return out;
    });
    const want:any = {
      "The Gnasher": ['art/hd_the_gnasher.png', 'own-sprite'],
      "The Minotaur": ['art/hd_the_minataur.png', 'own-sprite'],
      "Witchwild String": ['art/hd_whichwild_string.png', 'own-sprite'],
      "Death's Web": ['art/mr_deathsweb.png', 'own-icon'],
      "Stormshield": ['art/mr_stormshield.png', 'own-icon'],
      "Skin of the Vipermagi": ['art/mr_skinofthevipermagi.png', 'own-icon'],
      "Goldstrike Arch": ['art/hd_long_war_bow.png', 'base-sprite'],
      "Tal Rasha's Guardianship": ['art/hd_gothic_plate.png', 'base-sprite'],
      "Sander's Paragon": ['art/hd_cap_hat.png', 'base-sprite'],
      "Aldur's Rhythm": ['art/hd_morning_star.png', 'base-sprite'],
      "Civerb's Ward": ['art/hd_large_shield.png', 'base-sprite'],
    };
    for (const n of Object.keys(want)){
      expect(r[n], n).toEqual([want[n][0], want[n][0], want[n][1]]);
    }
    expect(errs).toEqual([]);
  });
});
