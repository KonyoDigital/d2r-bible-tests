import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v406 — every spawnable unique/set item resolves to its true in-game HD base sprite (art/hd_*.png),
// extracted from the local CASC install. Wins over mr_/d2io_/base_ backups; preserves existing hd_ art.
test.describe('v406 HD art for uniques + sets', () => {
  test('uniques + sets across slots resolve to art/hd_*.png', async ({ page }) => {
    const errs:string[]=[];
    page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
    page.on('pageerror',e=>errs.push(e.message));
    await page.goto(URL); await page.waitForTimeout(1500);
    const r = await page.evaluate(() => {
      const w:any = window;
      // actual droppable items across slots, incl. internal-codename uniques + the McAuley=Sander's
      // and Aldur's-Gauntlet=Rhythm / TalRasha-HowlingWind=Guardianship renames. NOT "Sander's Folly"
      // — that's the set NAME aggregate, not an item, so it keeps its set art.
      const names = ["The Gnasher","Goldstrike Arch","Death's Web","Tal Rasha's Guardianship",
                     "Sander's Paragon","Aldur's Rhythm","The Minotaur",
                     "Witchwild String","Stormshield","Skin of the Vipermagi","Civerb's Ward"];
      const out:any = {};
      for (const n of names){ try { out[n] = (typeof w.artUrl==='function') ? w.artUrl(n) : null; } catch(e){ out[n]='ERR'; } }
      return out;
    });
    const vals = Object.values(r) as string[];
    const hd = vals.filter(v => typeof v==='string' && v.indexOf('art/hd_')===0).length;
    // every one of the 11 actual items should now be HD
    expect(hd).toBe(11);
    expect(errs).toEqual([]);
  });
});
