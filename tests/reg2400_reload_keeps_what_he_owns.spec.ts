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

// REG-2403 — the review of REG-2401: with ONE gone screenshot waiting, his manual Scan sent two new screenshots to the
// menu, and the menu marked them read before he chose (v584.1's restart trap, back). tests/v212_folder_watch.spec.ts' guard
// for v584.1 has no gone file. The node half: tv/test_a_scan_reads_what_it_marks.py.
test('a manual folder scan reads its new screenshots at once while a gone one waits, and the menu marks nothing (REG-2403)', async ({ page }) => {
  const reads: string[] = [];
  const ITEM: Record<string, string> = { [FRAME]: 'Death Loop', 'new_1.png': 'Havoc Finger', 'new_2.png': 'Wraith Grasp' };
  await page.route('**/api/intake', (route) => {
    let file = '';
    try { file = String((route.request().postDataJSON() || {}).file || ''); } catch (e) {}
    if (file) reads.push(file);
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ITEM[file] ? [ITEM[file]] : [], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) });
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
  /* GrokBot's frame read Death Loop, which then left owned with nothing on record: a 'gone' screenshot in his folder */
  await page.evaluate(async ({ name, b64 }) => {
    const w: any = window;
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    await w.vaultIntake([new File([bytes], name, { type: 'image/jpeg', lastModified: 1 })], { fromTv: true });
    (eval('owned') as Set<string>).delete('Death Loop'); w.persistOwned();
    const mk = (n: string, t: number) => ({ kind: 'file', name: n,
      getFile: async () => new File([bytes], n, { type: 'image/jpeg', lastModified: t }) });
    w.showDirectoryPicker = async () => ({ queryPermission: async () => 'granted', requestPermission: async () => 'granted',
      values: async function* () { yield mk(name, 1); yield mk('new_1.png', 2); yield mk('new_2.png', 3); } });
  }, { name: FRAME, b64: TINY_JPG_B64 });
  reads.length = 0;
  await page.evaluate(() => (window as any).vaultConnectFolder());   // connecting runs his manual 🔄 Scan
  await page.waitForFunction(() => {
    const s = JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}');
    return !!(s['new_1.png'] && s['new_1.png'].held && s['new_2.png'] && s['new_2.png'].held);
  }, undefined, { timeout: 15000 });
  expect(reads.filter((f) => f === 'new_1.png').length, 'new_1.png was marked read and never read').toBeGreaterThan(0);
  expect(reads.filter((f) => f === 'new_2.png').length, 'new_2.png was marked read and never read').toBeGreaterThan(0);
  expect(reads.filter((f) => f === FRAME).length, 'the scan read the gone screenshot without his choice').toBe(0);
  /* his next Scan: nothing new — the gone one is offered as its own choice, and showing the menu writes nothing */
  const r = await page.evaluate(async () => {
    const w: any = window;
    const before = localStorage.getItem('d2r_intakeSeen');
    let menu = '';
    for (let i = 0; i < 20; i++) {           // the 12 s watch may hold the scan mutex for a moment
      await w.vaultScanFolder();
      menu = document.getElementById('vault-intake-report')?.textContent || '';
      if (/read which/.test(menu)) break;
      await new Promise((res) => setTimeout(res, 150));
    }
    return { menu, same: localStorage.getItem('d2r_intakeSeen') === before };
  });
  expect(r.menu).toContain('0 new');
  expect(r.menu, 'the gone screenshot is not offered as its own choice').toContain('Read again 1');
  expect(r.same, 'the menu wrote the scan ledger before any pick').toBe(true);
});

// REG-2404 — the Magic & Rare ✕ deleted the record only; the owned name stayed, and REG-2400's doctor kept it for good
// ("1 item you own ... a reload never drops what you own"). The node half: tv/test_every_removal_door_leaves_his_word.py.
test('a Magic & Rare toss takes the keeper out of owned on record, its undo is whole, and a reload never brings it back (REG-2404)', async ({ page }) => {
  await page.addInitScript(() => {
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      if (!localStorage.getItem('reg2404_seeded')) {
        localStorage.setItem('reg2404_seeded', '1');
        localStorage.setItem('d2r_ownerClaim', '*');
        localStorage.setItem('d2r_owned', JSON.stringify(['Enigma', 'Death Loop']));
        localStorage.setItem('d2r_magicFinds', JSON.stringify({ 'Death Loop': { q: 'rare', base: 'Ring', mods: ['+1 to All Skills'] } }));
      }
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).vaultThrowFind === 'function' && typeof (window as any).vaultRestoreLast === 'function');
  const t = await page.evaluate(() => {
    const w: any = window;
    const has = () => (eval('owned') as Set<string>).has('Death Loop');
    const rec = () => !!(eval('magicFinds') as any)['Death Loop'];
    const before = { owned: has(), magic: rec() };
    w.vaultThrowFind('Death Loop');                      // his ✕ on the MAGIC & RARE row
    const log = JSON.parse(localStorage.getItem('d2r_vaultRemoved') || '[]');
    const last = log[log.length - 1] || {};
    const tossed = { owned: has(), magic: rec(), stored: JSON.parse(localStorage.getItem('d2r_owned') || '[]'),
                     lane: last.lane, names: last.names, carries: !!(last.magic && last.magic['Death Loop']) };
    w.vaultRestoreLast();                                 // the undo
    const undone = { owned: has(), magic: rec() };
    w.vaultThrowFind('Death Loop');                      // and he throws it out for real
    return { before, tossed, undone };
  });
  expect(t.before).toEqual({ owned: true, magic: true });
  expect(t.tossed.owned, "the ✕ left the keeper's name in owned").toBe(false);
  expect(t.tossed.magic).toBe(false);
  expect(t.tossed.stored).not.toContain('Death Loop');
  expect([t.tossed.lane, t.tossed.names, t.tossed.carries], 'the toss did not go through the removal door whole')
    .toEqual(['card-click', ['Death Loop'], true]);
  expect(t.undone, 'the undo came back without the Magic & Rare record').toEqual({ owned: true, magic: true });

  await page.reload();
  await page.waitForFunction(() => typeof (window as any).vaultThrowFind === 'function');
  const r = await page.evaluate(() => ({ owned: (eval('owned') as Set<string>).has('Death Loop'),
                                         kept: ((window as any)._ownedLoadReceipt || {}).kept || [] }));
  expect(r.owned, 'the tossed keeper came back on the reload').toBe(false);
  expect(r.kept, 'the Vault calls a tossed keeper an item he owns').not.toContain('Death Loop');
});

// REG-2405 — his un-tick of a non-grail item deleted straight out of owned with no journal row, so REG-2401's verdict
// read its frame 'gone' and a re-feed brought it back. The node half: tv/test_every_removal_door_leaves_his_word.py.
test('his un-tick of a non-grail item is on record, so a re-feed of its frame never brings it back (REG-2405)', async ({ page }) => {
  let calls = 0;
  await page.route('**/api/intake', (route) => {
    calls++;
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ['Death Loop'], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) });
  });
  await page.addInitScript(() => {
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      if (!localStorage.getItem('reg2405_seeded')) {
        localStorage.setItem('reg2405_seeded', '1');
        localStorage.setItem('d2r_ownerClaim', '*');
        localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
        localStorage.removeItem('d2r_intakeSeen');
      }
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).vaultIntake === 'function' && typeof (window as any).toggleOwned === 'function');
  const feed = () => page.evaluate(async ({ name, b64 }) => {
    const w: any = window;
    w.switchTab && w.switchTab('tools');
    if (w.LSR && typeof w.LSR.setItem === 'function') w.LSR.setItem('d2r_vaultAutoIntake', 'on');
    else localStorage.setItem('d2r_vaultAutoIntake', 'on');
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    await w.vaultIntake([new File([bytes], name, { type: 'image/jpeg' })], { fromTv: true });
    return { owned: (eval('owned') as Set<string>).has('Death Loop'),
             report: document.getElementById('vault-intake-report')?.textContent || '' };
  }, { name: FRAME, b64: TINY_JPG_B64 });

  const first = await feed();
  expect(first.owned, 'PREMISE: the frame read put Death Loop in the vault').toBe(true);
  const u = await page.evaluate(() => {
    const w: any = window;
    w.toggleOwned('Death Loop');                         // his un-tick on its card - no grail unique: the non-grail branch
    const log = JSON.parse(localStorage.getItem('d2r_vaultRemoved') || '[]');
    const last = log[log.length - 1] || {};
    return { owned: (eval('owned') as Set<string>).has('Death Loop'), lane: last.lane, names: last.names, keepFiling: last.keepFiling };
  });
  expect(u.owned).toBe(false);
  expect([u.lane, u.names, u.keepFiling], 'the un-tick did not go through the removal door').toEqual(['un-tick', ['Death Loop'], true]);
  const before = calls;
  const again = await feed();
  expect(calls, 'a re-feed read the frame over his un-tick').toBe(before);
  expect(again.owned, 'a re-feed brought back the item he un-ticked').toBe(false);
  expect(again.report).toContain('your removal stands');
});
