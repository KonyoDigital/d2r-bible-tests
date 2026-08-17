// SKIPPED (audit 2026-06-12): dev diagnostic with zero expect()s — see picks_count_diag.
// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test.skip('capture all console + page errors', async ({ page }) => {
  page.on('pageerror', e => console.log('PAGEERR:', e.message, '|', e.stack?.split('\n').slice(0,3).join(' | ')));
  page.on('console', m => { if (m.type()==='error'||m.type()==='warning') console.log(m.type().toUpperCase()+':', m.text()); });
  await page.goto(BIBLE);
  await page.waitForTimeout(1500);
});
