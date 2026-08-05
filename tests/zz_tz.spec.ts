import { test } from '@playwright/test';
test('tz slot header heights', async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/tv/control_ui.html');
  await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const labs = Array.from(document.querySelectorAll('.tz-slot .tz-lab')) as HTMLElement[];
    const zones = Array.from(document.querySelectorAll('.tz-slot .tz-zones')) as HTMLElement[];
    return {
      labs: labs.map(l => ({ txt: (l.textContent||'').replace(/\s+/g,' ').trim().slice(0,34),
                             h: Math.round(l.getBoundingClientRect().height),
                             disp: getComputedStyle(l).display,
                             wrap: getComputedStyle(l).flexWrap })),
      zoneTops: zones.map(z => Math.round(z.getBoundingClientRect().top)),
    };
  });
  console.log('TZ| ' + JSON.stringify(r));
});
