import { test, expect } from '@playwright/test';

// REG-2220 — the vault evidence "👁 show the frame that witnessed it" proof opened "frame missing"
// though the reel was known (Ormus' Robes, flat id 1788820373017). A banked frame lives at
// hist/reel_<sid>/f_<ms>.jpg, but _vaultLookSrc built a path for only ONE of the three ways a look
// stores its frame: a reel-relative "reel_<sid>/f_<ms>" was refused by the /\// guard, and a BARE ms
// (reel in `session`) became "reel_<s>/<ms>" with no f_ prefix and no .jpg. Now all three resolve.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any)._vaultLookSrc === 'function');
});

test('_vaultLookSrc resolves every frame format to hist/reel_<sid>/f_<ms>.jpg', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._vaultLookSrc;
    return {
      bareMs:     f({ frame: '1788820373017', session: 's_1786385768689_67392' }),
      bareMsReel: f({ frame: '1788820373017', session: 'reel_s_1786385768689_67392' }),
      fPrefixed:  f({ frame: 'f_1788820373017.jpg', session: 's_9_9' }),
      reelRel:    f({ frame: 'reel_s_9_9/f_777' }),
      reelRelJpg: f({ frame: 'reel_s_9_9/f_777.jpg', session: null }),
      noReel:     f({ frame: '1788820373017', session: null }),
      noFrame:    f({ frame: '', session: 's_9_9' }),
    };
  });
  // a BARE ms + a reel sid (with or without the reel_ prefix) → the full f_<ms>.jpg path (REG-2220, Ormus)
  expect(r.bareMs).toBe('tv/frames/hist/reel_s_1786385768689_67392/f_1788820373017.jpg');
  expect(r.bareMsReel).toBe('tv/frames/hist/reel_s_1786385768689_67392/f_1788820373017.jpg');
  // an already-f_-prefixed-and-.jpg frame is unchanged (no regression for well-stored looks)
  expect(r.fPrefixed).toBe('tv/frames/hist/reel_s_9_9/f_1788820373017.jpg');
  // a reel-relative frame is served directly (was refused before), .jpg added if absent
  expect(r.reelRel).toBe('tv/frames/hist/reel_s_9_9/f_777.jpg');
  expect(r.reelRelJpg).toBe('tv/frames/hist/reel_s_9_9/f_777.jpg');
  // honest UNKNOWN: a bare frame with no reel cannot build a path (null, not a wrong guess)
  expect(r.noReel).toBeNull();
  expect(r.noFrame).toBeNull();
});
