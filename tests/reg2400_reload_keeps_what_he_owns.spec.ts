import { test, expect } from './_net_stub';

// REG-2400 + REG-2401 (#162 items 1 + 2, folded #144 item 6) — NOTHING HE OWNS IS SILENTLY LOST ON A RELOAD, AND A
// FRAME WHOSE ITEM SILENTLY LEFT IS READ AGAIN.
//
// GrokBot #230 on v3783 and again on v3784 (292 of his real frames, headless): d2r_owned 272 -> 113 on ONE reload, no
// journal row, no undo — and re-feeding all 292 frames added 0, because every frame said "already read". The lost names
// were rolled-name keepers (Death Loop, Wraith Grasp, Chaotic Grand Charm of Pestilence…) and the runewords typed
// "Ancient's Pledge" / "Breath of the Dying", which no catalogue on the page spells that way.
//
// This is the BROWSER half (CI runs it — never his Mac). The node laws hold the same code on the cut functions:
// tv/test_a_reload_never_drops_what_he_owns.py and tv/test_a_frame_is_read_again_when_its_item_is_gone.py.

const ROLLED = ['Chaotic Grand Charm of Pestilence', 'Sullied Grand Charm of Blight', 'Death Loop', 'Wraith Grasp',
                'Havoc Finger', 'Jewel of Daring'];          // no catalogue carries a rolled name, by construction
const LOST = ROLLED.concat(["Ancient's Pledge", 'Breath of the Dying']);   // #144 item 6 — typed runeword spellings
const CONTROL = 'Enigma';               // a runeword RUNEWORDS knows — never "kept", never dropped. Not a grail-seed
                                         // name, so the one-time seed cleanse (journaled, at load) never takes it mid-test
const FRAME = 'f_1790549355102.jpg';     // one of the frames GrokBot names in #162
const TINY_JPG_B64 =
  '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==';

const stored = (page: any) => page.evaluate(() => {
  try { return JSON.parse(localStorage.getItem('d2r_owned') || '[]'); } catch (e) { return null; }
});

test('a reload keeps every owned name no catalogue knows, and the Vault says so (REG-2400)', async ({ page }) => {
  await page.addInitScript(({ lost, ctrl }) => {
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      if (!localStorage.getItem('reg2400_seeded')) {        // seed ONCE: the reload below must read what the page wrote
        localStorage.setItem('reg2400_seeded', '1');
        localStorage.setItem('d2r_ownerClaim', '*');
        localStorage.setItem('d2r_owned', JSON.stringify([ctrl].concat(lost)));
        localStorage.removeItem('d2r_muleAssign');          // filed to NO mule, exactly as his frame reads were
        localStorage.removeItem('d2r_magicFinds');
      }
    } catch (e) {}
  }, { lost: LOST, ctrl: CONTROL });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function');

  for (const n of LOST.concat([CONTROL])) expect(await stored(page), n + ' left d2r_owned on the first load').toContain(n);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab && w.switchTab('tools');
    w.renderVault && w.renderVault();
    const el = document.getElementById('vault-owned-kept');
    return { kept: (w._ownedLoadReceipt || {}).kept || null, hidden: el ? el.hidden : null, text: el ? el.textContent : '' };
  });
  expect(r.kept, 'the load did not name what it kept').not.toBeNull();
  for (const n of ROLLED) expect(r.kept, n + ' is not named as kept').toContain(n);
  expect(r.kept, 'a name a catalogue knows was called a refusal').not.toContain(CONTROL);
  expect(r.hidden, 'the Vault keeps the refusal out of sight').toBe(false);
  expect(r.text).toContain('a reload never drops what you own');
  for (const n of ROLLED) expect(r.text, n + ' is kept but not on the Vault').toContain(n);

  await page.reload();
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function');
  for (const n of LOST.concat([CONTROL])) expect(await stored(page), n + ' left d2r_owned on the second load').toContain(n);
});

test('a frame read through the TV door survives a reload, is skipped while owned, read again once silently gone, and never over his removal (REG-2401)', async ({ page }) => {
  let calls = 0;
  await page.route('**/api/intake', (route) => {
    calls++;
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ['Death Loop'], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) });
  });
  await page.addInitScript(() => {
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      if (!localStorage.getItem('reg2401_seeded')) {
        localStorage.setItem('reg2401_seeded', '1');
        localStorage.setItem('d2r_ownerClaim', '*');
        localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
        localStorage.removeItem('d2r_intakeSeen');
      }
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).vaultIntake === 'function');

  /* the frame goes in the way the TV and the console hand it over: one File, fromTv */
  const feed = () => page.evaluate(async ({ name, b64 }) => {
    const w: any = window;
    w.switchTab && w.switchTab('tools');
    if (w.LSR && typeof w.LSR.setItem === 'function') w.LSR.setItem('d2r_vaultAutoIntake', 'on');
    else localStorage.setItem('d2r_vaultAutoIntake', 'on');
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    await w.vaultIntake([new File([bytes], name, { type: 'image/jpeg' })], { fromTv: true });
    const seen = (() => { try { return JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}'); } catch (e) { return null; } })();
    return { owned: (eval('owned') as Set<string>).has('Death Loop'), mark: seen ? seen[name] : null,
             report: document.getElementById('vault-intake-report')?.textContent || '' };
  }, { name: FRAME, b64: TINY_JPG_B64 });

  const first = await feed();
  expect(calls, 'the first read of the frame never reached the intake').toBeGreaterThan(0);
  expect(first.owned).toBe(true);
  expect(first.mark && first.mark.held, 'the ledger did not record what the frame put in the vault').toEqual(['Death Loop']);

  await page.reload();
  await page.waitForFunction(() => typeof (window as any).vaultIntake === 'function');
  expect(await stored(page), 'the frame read was dropped by the reload (GrokBot 272 -> 113)').toContain('Death Loop');

  const before = calls;
  const again = await feed();
  expect(calls, 'a frame whose item is still his was read (and billed) again').toBe(before);
  expect(again.report).toContain('Nothing new to read');

  /* a silent loss — the shape of the old reload drop: the name leaves owned with no removal on record */
  await page.evaluate(() => { (eval('owned') as Set<string>).delete('Death Loop'); (window as any).persistOwned(); });
  const healed = await feed();
  expect(calls, 'a frame whose item silently left was not read again — the loss never heals').toBeGreaterThan(before);
  expect(healed.owned, 'reading it again did not bring the item back').toBe(true);
  expect(healed.report).toContain('read again');

  /* HIS removal: dated and journaled — a re-feed must not bring it back */
  await page.evaluate(() => (window as any).vaultRemove(['Death Loop'], { lane: 'manual', quiet: true, why: 'REG-2401 spec' }));
  const afterHealed = calls;
  const removed = await feed();
  expect(calls, 'a re-feed read an item he removed').toBe(afterHealed);
  expect(removed.owned, 'a re-feed brought back an item he removed').toBe(false);
  expect(removed.report).toContain('your removal stands');
});

test('the folder picker offers a screenshot whose item silently left as its own choice (REG-2401)', async ({ page }) => {
  let calls = 0;
  await page.route('**/api/intake', (route) => {
    calls++;
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ['Death Loop'], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) });
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForTimeout(1800);
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    const w: any = window;
    if (w.LSR && typeof w.LSR.setItem === 'function') w.LSR.setItem('d2r_vaultAutoIntake', 'on');
    else localStorage.setItem('d2r_vaultAutoIntake', 'on');
    w.switchTab('tools'); w.renderVault();
  });
  const r = await page.evaluate(async ({ name, b64 }) => {
    const w: any = window;
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    const mk = () => new File([bytes], name, { type: 'image/jpeg', lastModified: 1790549355102 });
    await w.vaultIntake([mk()], { fromTv: true });
    (eval('owned') as Set<string>).delete('Death Loop'); w.persistOwned();
    w.vaultScanFolderLegacy([mk()]);
    const menu = document.getElementById('vault-intake-report')?.textContent || '';
    return { menu };
  }, { name: FRAME, b64: TINY_JPG_B64 });
  expect(r.menu, 'the gone screenshot is not offered as its own choice').toContain('Read again 1');
  expect(r.menu, 'a gone screenshot was folded into "New"').toContain('0 new');
  const before = calls;
  await page.evaluate(() => (window as any).vaultReadBatch('gone'));
  await page.waitForFunction(() => (eval('owned') as Set<string>).has('Death Loop'), undefined, { timeout: 10000 });
  expect(calls, 'Read again did not read the screenshot').toBeGreaterThan(before);
});
