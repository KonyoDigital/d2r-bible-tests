import { test, expect } from '@playwright/test';

// REG-2233 (#75, GrokBot "top priority") — A REGISTERED MAGIC & RARE KEEPER IN `owned` IS SILENTLY
// PRUNED ON RELOAD. The AI Item Checker's "Mule it (keep)" (aicMule, bible.html:44913), the planner's
// magic/rare pick (vaultPlannerFile) and aicJudgeApply all write magicFinds[name] AND owned.add(name)
// — the comment at bible.html:45085 states the intent: "Own the name so the count moves." By the
// v3716 "one home" doctrine none of them files the keeper to a mule. But the load-time owned-prune
// (bible.html:24917) rebuilds `owned`, keeping a name only if a grail/base catalogue (ITEM_REGISTRY,
// _UNI_EXTRA, _GRAIL_SEED, _EXTRA_ITEM_SET, _ROSTER_NORM, set pieces, d2rCatalogueKnows) OR the mule
// map (_maKeep = d2r_muleAssign) recognises it — it NEVER consults the Magic & Rare register
// (magicFinds). So a charm or jewel he kept survives one load and is rebuilt away on the next: the
// exact silent drop that prune's own note (bible.html:24904) calls "the failure mode". The fix adds
// _maMagic (magicFinds) to the survival set, the same way _maKeep reads the mule map.
//
// Faithful seed (the on-disk shape after a keep): d2r_magicFinds holds the keeper's record (its
// home) and d2r_owned holds the same name (the owned row the keep adds), with NO d2r_muleAssign row.
// Stone of Jordan is the no-regression control — a real grail unique the prune must always keep.
//
// RED without the fix: after one reload the keepers are gone from d2r_owned (pruned); the control
// survives. GREEN with the fix: the keepers stay in d2r_owned AND in d2r_magicFinds; control stays.
//
// (On HEAD the keeper's magicFinds record and FIND already persist — v3718's union/draw landed — so
// this guards the LAST un-saved half of the add: the owned receipt. Verified in node before writing.)

const KEEPER_RARE  = 'Blood Scarab';                   // a rolled rare jewel — no catalogue knows it (grep: 0 in bible.html)
const KEEPER_MAGIC = 'Shimmering Small Charm of Vita'; // a rolled magic charm — no catalogue knows it
const CONTROL      = 'The Stone of Jordan';            // a real grail unique (catalogue keys it WITH "The") — must survive the prune

test.beforeEach(async ({ page }) => {
  await page.addInitScript(({ kr, km, ctrl }) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_magicFinds', JSON.stringify({
        [kr]: { q: 'rare',  base: 'Jewel',       mods: ['15% Increased Attack Speed', '-15 to Requirements'] },
        [km]: { q: 'magic', base: 'Small Charm', mods: ['All Resistances +5', '+20 to Life'] },
      }));
      localStorage.setItem('d2r_owned', JSON.stringify([ctrl, kr, km]));
      localStorage.removeItem('d2r_muleAssign'); // the keepers are filed to NO mule (v3716 "one home")
    } catch (e) {}
  }, { kr: KEEPER_RARE, km: KEEPER_MAGIC, ctrl: CONTROL });
  await page.goto('file://' + process.cwd() + '/bible.html');
  // suggestMule is assigned (bible.html:40951) AFTER the load-time owned-prune (:24917), so once it
  // exists the prune has already run on the seeded store.
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function');
});

test('a registered Magic & Rare keeper in owned survives the load-time prune (REG-2233, #75)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const read = (k: string) => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
    return { owned: read('d2r_owned') || [], magicKeys: Object.keys(read('d2r_magicFinds') || {}) };
  });

  // the keeper's HOME (magicFinds) is intact — the half that already persists on HEAD
  expect(r.magicKeys, 'magicFinds keeps the rare keeper').toContain(KEEPER_RARE);
  expect(r.magicKeys, 'magicFinds keeps the magic keeper').toContain(KEEPER_MAGIC);
  // no-regression + proof the prune actually ran and is selective: a real unique is never dropped
  expect(r.owned, 'a real grail unique is never pruned').toContain(CONTROL);
  // THE LAW: the keeper's owned row is NOT silently dropped on reload (RED before the fix)
  expect(r.owned, 'the rare keeper stays in owned after reload').toContain(KEEPER_RARE);
  expect(r.owned, 'the magic keeper stays in owned after reload').toContain(KEEPER_MAGIC);
});
