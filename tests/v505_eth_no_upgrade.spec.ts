import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v505 — ethereal items can't be cube-upgraded, so an ethereal Normal/Exceptional base must NOT appear
// in the Forge's base tier-upgrade bucket (it stays a socket-&-forge-as-is base). Same rule as v486/v487.
async function upgradesFor(page: any, base: string, ethereal: boolean) {
  await page.addInitScript((s: any) => {
    localStorage.setItem('d2r_owned', JSON.stringify([s.base]));
    localStorage.setItem('d2r_ethereal', JSON.stringify(s.eth ? [s.base] : []));
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, { base, eth: ethereal });
  await page.goto(URL);
  await page.waitForTimeout(1300);
  return await page.evaluate((b: string) => {
    const w: any = window;
    w._ensureSocketBaseEntry(b);
    const s = w.forgeScan();
    return (s.upgrades || []).filter((u: any) => u.base && /Broad Sword/.test(u.base.base)).length;
  }, base);
}

// v534 — the upgrade bucket is GONE: NO white base (normal, superior, OR ethereal) can be cube-upgraded to a
// higher tier (game-file cubemain.txt: unique/rare/set only). Both now produce zero upgrade entries.
test('a NON-ethereal Normal white base produces NO upgrade entry (v534 — bucket removed)', async ({ page }) => {
  const n = await upgradesFor(page, 'Broad Sword (Larzuk base)', false);
  expect(n).toBe(0);
});

test('an ETHEREAL Normal base also produces NO upgrade entry', async ({ page }) => {
  const n = await upgradesFor(page, 'Broad Sword (Larzuk base)', true);
  expect(n).toBe(0);
});
