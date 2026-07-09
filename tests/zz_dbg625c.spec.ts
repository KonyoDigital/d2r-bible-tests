import { test } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test('dbg3', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', JSON.stringify({ 'Breath of the Dying': 'Jul 9' }));
    localStorage.setItem('d2r_owned', JSON.stringify(['Phase Blade (Larzuk base)']));
    localStorage.setItem('d2r_rwBaseUsed', JSON.stringify({ 'Breath of the Dying': { l: 'Phase Blade (Larzuk base)', copy: true } }));
    const st: any = {};
    ['El','Eld','Tir','Nef','Eth','Ith','Tal','Ral','Ort','Thul','Amn','Sol','Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um','Mal','Ist','Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod'].forEach((n) => (st[n] = 4));
    localStorage.setItem('d2r_runeStash', JSON.stringify(st));
  });
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('forge'); try { w.renderForge(); } catch (e) {}
    const dom = (document.getElementById('forge-body') || document.body).innerHTML;
    const sc = w.forgeScan();
    return { pipePB: (sc.pipeline||[]).filter((t:any)=>/Phase/.test((t.base&&t.base.name)||'')).map((t:any)=>t.rw),
      chainInDom: /Larzuk-socket your/.test(dom),
      became: /already became/.test(dom),
      chainCtx: (dom.match(/Larzuk-socket your.{0,600}/)||['none'])[0].replace(/</g,'‹').slice(0,420) };
  });
  console.log('DBG', JSON.stringify(r, null, 1));
});
