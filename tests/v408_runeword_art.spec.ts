import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v408 — every forged runeword resolves to a representative HD base sprite (no blank ◆ white-dot tile).
test('runewords resolve to art/hd_*.png (no white-dot ◆)', async ({ page }) => {
  const errs:string[]=[];
  page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
  page.on('pageerror',e=>errs.push(e.message));
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w:any = window;
    const names = ['Enigma','Spirit','Call to Arms','Insight','Infinity','Grief','Chains of Honor','Heart of the Oak','Spirit','Stone'];
    const out:any = {};
    for (const n of names) out[n] = w.artUrl ? w.artUrl(n) : null;
    return out;
  });
  expect(r['Enigma']).toBe('art/hd_plate_mail.png');
  const hd = Object.values(r).filter(v => typeof v==='string' && (v as string).indexOf('art/hd_')===0).length;
  expect(hd).toBe(Object.keys(r).length);  // all resolve to HD
  expect(errs).toEqual([]);
});
