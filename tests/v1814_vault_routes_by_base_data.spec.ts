import { test, expect } from './_net_stub';
import * as path from 'path';

// v1814 — THE VAULT FILED ARMOUR IN THE WEAPONS LOCKER.
//
// Konyo, 2026-08-19: "some items here were incorrectly VAULTED and MULED ... make sure its routed
// correctly." His UNI-WEAPONS locker held six items and one of them was a gold horned face.
//
// suggestMule() decided the slot with ARMOR_RE, a list of WORDS tested against `base + ' ' + name`.
// A base whose name contains none of those words fell through to the weapons default. Measured
// through the real function, eight of them:
//
//   Andariel's Visage   Demonhead          (a helm)
//   Ormus' Robes        Dusk Shroud        (body armour)
//   Arkaine's Valor     Balrog Skin        (body armour)
//   Gladiator's Bane    Wire Fleece        (body armour)
//   Homunculus          Hierophant Trophy  (a necro shield)
//   Boneflame           Succubus Skull     (a necro shield)
//   Darkforce Spawn     Bloodlord Skull    (a necro shield)
//   Head Hunter's Glory Troll Nest         (a barb shield)
//
// And the mirror, which the same sweep found: weapons pulled INTO uni-armor because an armour word
// appears in their name — Astreon's Iron Ward (Caduceus) and Widowmaker (Ward Bow) on "ward", The
// Vile Husk (Tusk Sword) on "husk".
//
// Adding eight more words would have fixed eight items and left the next one for him to find.
// BASE_DB already knows: armour bases carry a `defense` range, weapons carry `oneH`/`twoH`. The
// data decides now; the keyword list survives only for what the table cannot classify — belts and
// sashes carry NEITHER field, which is why they are asserted here too.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const ARMOUR_IN_WEAPONS = [
  "Andariel's Visage", "Ormus' Robes", "Arkaine's Valor",
  'Homunculus', 'Boneflame', 'Darkforce Spawn', "Head Hunter's Glory",
];
const WEAPONS_IN_ARMOUR = ["Astreon's Iron Ward", 'The Vile Husk', 'Widowmaker'];
const BELTS = ['Goldwrap', 'Nightsmoke', 'Lenymo', 'Snakecord'];

async function routes(page: any, names: string[]) {
  return page.evaluate((ns: string[]) => {
    const w = window as any;
    return ns.map((n) => {
      let id = '';
      try { id = (w.suggestMule(n) || {}).id || ''; } catch (e) { id = 'THREW'; }
      const tip = w.ITEM_TIP ? w.ITEM_TIP[n] : null;
      const b = (tip && tip.b) || '';
      const rec = b && w._baseRec ? w._baseRec(b) : null;
      return { n, b, id, armour: !!(rec && rec.defense), weapon: !!(rec && (rec.oneH || rec.twoH)) };
    });
  }, names);
}

test.beforeEach(async ({ page }) => {
  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function', null, { timeout: 20000 });
});

test('v1814 — armour whose base name carries no armour word still lands in UNI-ARMOR', async ({ page }) => {
  for (const r of await routes(page, ARMOUR_IN_WEAPONS)) {
    expect(r.armour, `${r.n} (${r.b}) must be armour in BASE_DB, or this test is asserting the wrong thing`).toBe(true);
    expect(r.id, `${r.n} (${r.b})`).toBe('uni-armor');
  }
});

test('v1814 — a weapon is not dragged into UNI-ARMOR by a word in its name', async ({ page }) => {
  for (const r of await routes(page, WEAPONS_IN_ARMOUR)) {
    expect(r.weapon, `${r.n} (${r.b}) must be a weapon in BASE_DB`).toBe(true);
    expect(r.id, `${r.n} (${r.b})`).toBe('uni-weap');
  }
});

test('v1814 — belts still route by the keyword list, which BASE_DB cannot replace', async ({ page }) => {
  // Belts and sashes have neither a defense range nor a damage range. If the keyword fallback were
  // ever removed in favour of "just use BASE_DB", every belt in the game would land in UNI-WEAPONS.
  for (const r of await routes(page, BELTS)) {
    expect(r.armour, `${r.n} (${r.b}) is expected to be undecidable from BASE_DB`).toBe(false);
    expect(r.weapon, `${r.n} (${r.b}) is expected to be undecidable from BASE_DB`).toBe(false);
    expect(r.id, `${r.n} (${r.b})`).toBe('uni-armor');
  }
});

test('v1814 — no roster item contradicts its own base data, in either direction', async ({ page }) => {
  // the sweep that found the eight. It is the whole point: a spot-check on named items would pass
  // again the day a new base is added that no keyword happens to match.
  const bad = await page.evaluate(() => {
    const w = window as any;
    const names: string[] = typeof w._gUniqueRoster === 'function' ? w._gUniqueRoster() : [];
    const out: string[] = [];
    for (const n of names) {
      let sg: any = null;
      try { sg = w.suggestMule(n); } catch (e) { continue; }
      if (!sg) continue;
      const tip = w.ITEM_TIP ? w.ITEM_TIP[n] : null;
      const b = (tip && tip.b) || '';
      const rec = b && w._baseRec ? w._baseRec(b) : null;
      if (!rec) continue;
      if (sg.id === 'uni-weap' && rec.defense) out.push(`ARMOUR in weapons: ${n} (${b})`);
      if (sg.id === 'uni-armor' && !rec.defense && (rec.oneH || rec.twoH)) out.push(`WEAPON in armor: ${n} (${b})`);
    }
    return { total: names.length, bad: out };
  });
  expect(bad.total, 'the roster must be non-empty or this proves nothing').toBeGreaterThan(300);
  expect(bad.bad, 'items filed against their own base data').toEqual([]);
});

test('v1814 — the migration repairs old assignments WITHOUT touching his own choices', async ({ page, context }) => {
  // suggestMule only decides the NEXT item; an assignment already in d2r_muleAssign is pinned, and
  // that pinned copy is what he is looking at. The migration must fix those — and stop there.
  await context.addInitScript(() => {
    // v1518's guard is right and this spec tripped it: spoofing navigator.webdriver identifies the
    // page as the SUITE, which v1499 treats as a GUEST — every bare key seeded below would land in
    // an I·<id>· world the app never reads, and the assertions would be interrogating a world that
    // does not exist. Claim the owner world in the same breath as the spoof.
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    try { Object.defineProperty(navigator, 'webdriver', { get: () => true }); } catch (e) {}
    try {
      localStorage.setItem('d2r_muleAssign', JSON.stringify({
        "Andariel's Visage": 'uni-weap',      // mis-filed armour, BASE_DB-decisive → must move
        'Homunculus': 'uni-weap',             // mis-filed shield, BASE_DB-decisive → must move
        "Astreon's Iron Ward": 'uni-armor',   // mis-filed weapon, BASE_DB-decisive → must move
        // v1815 — THE CASE THE FIRST MIGRATION MISSED. A belt has neither a defense nor a damage
        // range, so a migration that asked BASE_DB directly left a mis-pinned Goldwrap in the
        // WEAPONS locker while suggestMule would have said armour. Two rules, two answers, no
        // way for a reader to say which was right. The migration asks the router now.
        'Goldwrap': 'uni-weap',               // mis-filed belt, keyword-only → must move
        'Nightsmoke': 'uni-weap',             // mis-filed belt, keyword-only → must move
        'Blackhand Key': 'uni-weap',          // correct → must stay
        'Shaftstop': 'uni-armor',             // correct → must stay
        "Titan's Revenge": 'shared',          // HIS choice → must stay
        "Nord's Tenderizer": 'wip',           // HIS choice → must stay
      }));
    } catch (e) {}
  });
  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function', null, { timeout: 20000 });

  const a = await page.evaluate(() => {
    try { return JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'); } catch (e) { return {}; }
  });
  expect(a["Andariel's Visage"]).toBe('uni-armor');
  expect(a['Homunculus']).toBe('uni-armor');
  expect(a["Astreon's Iron Ward"]).toBe('uni-weap');
  expect(a['Blackhand Key']).toBe('uni-weap');
  expect(a['Shaftstop']).toBe('uni-armor');
  expect(a['Goldwrap'], 'a belt is keyword-routed — the migration must still repair it').toBe('uni-armor');
  expect(a['Nightsmoke'], 'the same, for the second belt').toBe('uni-armor');
  expect(a["Titan's Revenge"], 'SHARED is a judgement call, not a slot').toBe('shared');
  expect(a["Nord's Tenderizer"], 'WIP is a judgement call, not a slot').toBe('wip');
});

test('v1816 — the repair runs ONCE, and after it his hand wins', async ({ page, context }) => {
  // As shipped in v1815 this ran on every load, which quietly made it the thing its own comment
  // forbids: a migration that overrules a judgement call. Inside the uni-weap/uni-armor pair the
  // router is usually right but not always — an Infinity polearm he keeps beside his armour, a
  // shield he files with the weapons because that is where he looks for it. Each would have been
  // dragged back on every reload, forever, with nothing saying why. A repair is an event; a rule
  // that re-asserts itself is a policy, and he did not ask for a policy.
  await context.addInitScript(() => {
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    try { Object.defineProperty(navigator, 'webdriver', { get: () => true }); } catch (e) {}
    try {
      if (!localStorage.getItem('__seeded')) {
        localStorage.setItem('d2r_muleAssign', JSON.stringify({
          "Andariel's Visage": 'uni-weap',   // mis-filed → the one-time repair must move it
          'Blackhand Key': 'uni-weap',       // correct → untouched
        }));
        localStorage.setItem('__seeded', '1');
      }
    } catch (e) {}
  });

  const assign = async () => page.evaluate(() => {
    try { return JSON.parse((window as any).LSR.getItem('d2r_muleAssign') || '{}'); } catch (e) { return {}; }
  });

  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function', null, { timeout: 20000 });
  await page.waitForFunction(() => {
    try { return !!(window as any).LSR.getItem('d2r_vaultRerouteDone'); } catch (e) { return false; }
  }, null, { timeout: 20000 });
  expect((await assign())["Andariel's Visage"], 'the one-time repair should have moved it').toBe('uni-armor');

  // HIS HAND: deliberately put it back in the weapons locker
  await page.evaluate(() => {
    const w = window as any;
    const a = JSON.parse(w.LSR.getItem('d2r_muleAssign') || '{}');
    a["Andariel's Visage"] = 'uni-weap';
    w.LSR.setItem('d2r_muleAssign', JSON.stringify(a));
  });

  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function', null, { timeout: 20000 });
  await page.waitForTimeout(1500);

  expect((await assign())["Andariel's Visage"],
    'the migration ran a second time and overruled a placement he made by hand').toBe('uni-weap');
});

test('v1816 — the done-flag is profile-forked, like the map it guards', async () => {
  // d2r_muleAssign is per-profile (MAIN / LADDER). A shared done-flag would mean repairing MAIN
  // marks LADDER complete and leaves its vault untouched — a profile toggle silently changing
  // what got fixed, which is the one thing the ladder doctrine forbids.
  const fs = await import('fs');
  const bible = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
  const m = /window\._LP_FORKED = new Set\(\[(.*?)\]\)/s.exec(bible);
  expect(m, '_LP_FORKED could not be found — this guard is protecting nothing').toBeTruthy();
  const keys = (m as RegExpExecArray)[1].match(/"([^"]+)"/g)!.map((x) => x.replace(/"/g, ''));
  expect(keys, 'the map itself must be forked, or this test is asserting the wrong thing')
    .toContain('d2r_muleAssign');
  expect(keys, 'the done-flag must be forked alongside the map it guards')
    .toContain('d2r_vaultRerouteDone');
});
