import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v403 — a QUANTITY base owned ×N occupies N SEPARATE slots in the in-game stash replica (Konyo's 3 Threshers
// = 3 cells, packed alongside the other units). The header/goldbox count the PHYSICAL total. Capped at 3.
test('v403 a base owned x3 renders 3 separate slots in the mule replica', async ({ page }) => {
  const errs: string[] = [];
  page.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL); await page.waitForTimeout(1200);
  const r = await page.evaluate(() => {
    const w = window as any;
    // register a quantity base (cat 'Socketed bases' so ownedPool keeps it) ×3 + a single base
    w.EXTRA_ITEMS['Thresher (Larzuk base)'] = { cat: 'Socketed bases', slot: 'Weapon' };
    w.EXTRA_ITEMS['Grim Scythe (6os)'] = { cat: 'Socketed bases', slot: 'Weapon' };
    eval("owned.add('Thresher (Larzuk base)'); copies['Thresher (Larzuk base)']=3; owned.add('Grim Scythe (6os)');");
    w.vaultAssign('Thresher (Larzuk base)','bases'); w.vaultAssign('Grim Scythe (6os)','bases');
    w.openMuleCard('bases');
    const box = document.getElementById('vault-detail');
    const items = box ? Array.from(box.querySelectorAll('.vd-item')) : [];
    const thresherSlots = items.filter(el => (el.getAttribute('title')||'').indexOf('Thresher') === 0).length;
    const grimSlots = items.filter(el => (el.getAttribute('title')||'').indexOf('Grim Scythe') === 0).length;
    const sub = (box?.querySelector('.vd-sub')?.textContent)||'';
    const gold = (Array.from(box?.querySelectorAll('.vd-goldbox')||[]).map(e=>e.textContent).join(' '))||'';
    w.vaultCloseCard && w.vaultCloseCard();
    return { thresherSlots, grimSlots, sub, gold };
  });
  expect(r.thresherSlots).toBe(3);
  expect(r.grimSlots).toBe(1);
  expect(r.sub).toContain('4 items');
  expect(r.gold).toContain('4 on this mule');   // v405 — goldbox now reports stash/mule counts
  expect(errs).toEqual([]);
});

// the replica caps at 3 even if more copies somehow exist (over-cap copies are thrown out at intake)
test('v403 replica shows at most 3 slots for a base even if copies exceeds the cap', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1200);
  const n = await page.evaluate(() => {
    const w = window as any;
    w.EXTRA_ITEMS['Thresher (Larzuk base)'] = { cat: 'Socketed bases', slot: 'Weapon' };
    eval("owned.add('Thresher (Larzuk base)'); copies['Thresher (Larzuk base)']=5;");
    w.vaultAssign('Thresher (Larzuk base)','bases');
    w.openMuleCard('bases');
    const box = document.getElementById('vault-detail');
    const c = box ? Array.from(box.querySelectorAll('.vd-item')).filter(el => (el.getAttribute('title')||'').indexOf('Thresher')===0).length : -1;
    w.vaultCloseCard && w.vaultCloseCard();
    return c;
  });
  expect(n).toBe(3);
});
