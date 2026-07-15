import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v562 — two fixes from Konyo's 2026-07-04 cow-run screenshots + request:
// (1) BLUE-MAGIC LEAK: the live KonyoEndgame filter's hide lists were static complements of the OLD ~50-base
//     draft — the wanted bases, all 4 circlets and stale drafts (Monarch/Colossus Blade…) matched NO rule, and
//     the mod default-shows unmatched items → magic Gothic Shield / magic Coronet showed on the ground. Now the
//     hide lists rebuild LIVE and tail rules hide magic/rare copies of wanted bases + non-rare circlets.
// (2) CHRONICLE-SYNCED KEEP-OR-THROW: the vault's throw-out / mule decisions read d2r_rwMade (the Chronicle)
//     like the Forge/Smart-AI already do — a base whose every hostable runeword is ✓ forged → __throwout.

test('loot filter: no blue-magic leak — every real base code is hidden at magic rarity', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const CODE = JSON.parse(document.getElementById('lf-base-codes')!.textContent!);
    const QUEST = new Set(['hdm', 'hfh', 'hst', 'leg', 'msf', 'qf1', 'qf2', 'g33', 'd33']);
    const out = JSON.parse(w.buildEndgameFilter().text);
    const magicHidden = new Set<string>();
    out.rules.forEach((rl: any) => {
      if (rl.enabled && rl.ruleType === 'hide' && (rl.equipmentRarity || []).includes('magic'))
        (rl.equipmentItemCode || []).forEach((c: string) => magicHidden.add(c));
    });
    const leaks: string[] = [];
    // v599 — ci3 (Diadem) is DELIBERATELY not magic-hidden: a blue Diadem is a chase item
    // (Konyo's Torrid Diadem of Amicae — +3 class skills / MF rolls on the elite circlet).
    // v690 — CRAFT INBOX: the four crafts' best-slot gear bases are the SECOND sanctioned magic
    // exemption (blues are craft fuel; their non-magic rarities are tail-hidden instead). Derive the
    // exemption set from the shipped rule so the spec tracks the whitelist, not a copy of it.
    const craftTail = out.rules.find((x: any) => x.name === 'Hide Craft Bases Non-Magic');
    const CRAFT = new Set<string>((craftTail && craftTail.equipmentItemCode) || []);
    Object.keys(CODE).forEach((nm) => { const c = CODE[nm]; if (!QUEST.has(c) && c !== 'ci3' && !CRAFT.has(c) && !magicHidden.has(c)) leaks.push(nm + '=' + c); });
    const ebAll = w._endgameFilterBases();
    const eb = ebAll.codes as string[];
    const trash = out.rules.find((x: any) => x.name === '1. Hide Trash Gear');
    // v592 — non-premium wanted bases are DELIBERATELY in the trash hide as plain drops (they show
    // eth/socketed only, via rule 3); only the premium floor may never be swallowed.
    const wantedInTrash = (ebAll.plainCodes as string[]).filter((c) => trash.equipmentItemCode.includes(c));
    const commonPlainHidden = eb.filter((c) => !ebAll.plainCodes.includes(c)).every((c) => trash.equipmentItemCode.includes(c));
    // rare circlets must survive (they show via "Show Rare Rings and Amulets"); no hide rule may catch them
    const rareCircHidden = out.rules.some((rl: any) => rl.enabled && rl.ruleType === 'hide'
      && (rl.equipmentRarity || []).includes('rare')
      && (rl.equipmentItemCode || []).some((c: string) => ['ci0', 'ci1', 'ci2', 'ci3'].includes(c)));
    const ethShow = out.rules.find((x: any) => x.name === '3. Show ETH and Socket bases');
    return {
      leaks, wantedInTrash, commonPlainHidden, rareCircHidden, ethRarity: ethShow.equipmentRarity,
      ci1MagicHidden: magicHidden.has('ci1'),           // Konyo's blue Coronet
      ci3MagicShown: !magicHidden.has('ci3'),           // v599 — blue Diadem = chase item, must SHOW
      gtsMagicHidden: magicHidden.has('gts'),           // Konyo's blue Gothic Shield — a HitPower craft shield since v690
      uitMagicHidden: magicHidden.has('uit'),           // stale-draft Monarch, previously in NO rule
    };
  });
  expect(r.leaks).toEqual([]);                          // every non-quest base code hides its magic version
  expect(r.wantedInTrash).toEqual([]);                  // premium plains NOT swallowed by the trash hide
  expect(r.commonPlainHidden).toBe(true);               // v592: every common wanted base hides its PLAIN drop
  expect(r.rareCircHidden).toBe(false);                 // rare circlets still show
  expect(r.ethRarity).toEqual(['normal', 'hiQuality']); // socketed MAGIC can't ride the eth/socket show rule
  expect(r.ci1MagicHidden).toBe(true);
  expect(r.ci3MagicShown).toBe(true);                   // v599 — blue Diadems surface (default-show, no rule matches)
  expect(r.gtsMagicHidden).toBe(false);   // v693.3 — Gothic Shield joined the v690 craft inbox (HitPower shield slot): its BLUES are fuel now, deliberately default-shown
  expect(r.uitMagicHidden).toBe(true);
});

test('vault: keep-or-throw reads the Chronicle — all words forged → __throwout, unmade → kept + named', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const r = await page.evaluate(() => {
    const w: any = window;
    // empty Chronicle → a 6os COLOSSUS BLADE (elite — passes the v576 endgame-gear gate, unlike the
    // exceptional Grim Scythe) still serves Breath of the Dying → keeper
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    const before = w.suggestMule('Colossus Blade (6os)');
    // mark EVERY runeword made → no base serves anything any more
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => (made[n] = 'x'));
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    const after = w.suggestMule('Colossus Blade (6os)');
    const helperAllMade = (w._baseUnmadeRunewords('Monarch', 4) || []).length;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    const helperFresh = (w._baseUnmadeRunewords('Monarch', 4) || []).length;
    localStorage.removeItem('d2r_rwMade');
    return {
      beforeId: before && before.id, beforeWhy: String((before && before.why) || ''),
      afterId: after && after.id, afterWhy: String((after && after.why) || ''),
      helperAllMade, helperFresh,
    };
  });
  expect(r.beforeId).toBe('bases');
  expect(r.beforeWhy).toContain('still needed');        // the keep reason NAMES the unmade words
  expect(r.afterId).toBe('__throwout');                 // Chronicle-complete base → vendor, not mule
  expect(r.afterWhy).toMatch(/forged|nothing left/);
  expect(r.helperAllMade).toBe(0);                      // _baseUnmadeRunewords: all made → nothing left
  expect(r.helperFresh).toBeGreaterThan(0);             // fresh Chronicle → 4os Monarch words (Spirit…) pending
});

test('generic socketed labels + non-RW bases keep their v322/v524 routing (no regression)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const r = await page.evaluate(() => {
    const w: any = window; const sm = w.suggestMule;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));   // pin empty — don't drift with the live seed
    return {
      generic: sm('Socketed Body Armor') && sm('Socketed Body Armor').id,
      circlet: sm('Coronet (2os)') && sm('Coronet (2os)').id,
      monarch: sm('Monarch (4os)') && sm('Monarch (4os)').id,
    };
  });
  expect(r.generic).toBe('bases');       // EXTRA_ITEMS generic entries early-return, untouched by the sync
  expect(r.circlet).toBe('__throwout');  // circlets can't host runewords — unchanged
  expect(r.monarch).toBe('bases');       // 4os Monarch still serves Spirit etc. — kept
});
