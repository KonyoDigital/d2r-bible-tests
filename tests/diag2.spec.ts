// SKIPPED (audit 2026-06-12): dev diagnostic with zero expect()s — see picks_count_diag.
import { test } from '@playwright/test';
import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test.skip('capture all console + page errors', async ({ page }) => {
  page.on('pageerror', e => console.log('PAGEERR:', e.message, '|', e.stack?.split('\n').slice(0,3).join(' | ')));
  page.on('console', m => { if (m.type()==='error'||m.type()==='warning') console.log(m.type().toUpperCase()+':', m.text()); });
  await page.goto(BIBLE);
  await page.waitForTimeout(1500);
});
