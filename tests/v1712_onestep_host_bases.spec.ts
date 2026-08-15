import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1712 — ONE STEP · THE BASES THAT CAN HOST THIS WORD.
// Konyo asked for the Forge → 🟡 ONE STEP runeword hover card to name the base items the word can
// actually be made in, with HD art, instead of only the socket-class phrase ("4 socket Body Armor").
//
// Three things here are held by the gate rather than by discipline:
//
//  (a) THE VIEW GATE. The row belongs to ONE STEP only. A gate never seen to REFUSE is not a gate,
//      so the negative case is asserted as hard as the positive one.
//  (b) SOCKET FEASIBILITY. The meta engine's curated path does not socket-filter, and it offered
//      "Mage Plate" (max 3) as an endgame home for Chains of Honor, which needs 4 — a base that can
//      never hold that word, in a row whose whole job is telling him what to farm. Every DOM
//      assertion was green; only looking at the render caught it. This sweep is why it cannot return.
//  (c) ONE SOURCE OF TRUTH. The tiles must come from window._forgeMetaBase — the same function that
//      prints the "base:" label on the task row beside the tooltip. A second, independently derived
//      list is REG-076's defect exactly (the console kept a hand-copied copy of a routing rule and it
//      went stale), and v524's "no mismatches" doctrine forbids it.

test('(a) the base row renders in ONE STEP — and REFUSES in every other Forge view', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const rw = 'Bramble';
    const tip = w.RUNEWORD_TIP[w.findRuneword(rw)];
    const at = (tab: string, view: string) => {
      document.documentElement.setAttribute('data-active-tab', tab);
      w._FORGE_VIEW = view;
      return String(w._rwTipHtml(tip, rw) || '').indexOf('att-bases') >= 0;
    };
    return {
      onestep: at('forge', 'onestep'),
      all: at('forge', 'all'),
      now: at('forge', 'now'),
      completed: at('forge', 'completed'),
      otherTab: at('session', 'onestep'),
      noName: (function () {
        document.documentElement.setAttribute('data-active-tab', 'forge');
        w._FORGE_VIEW = 'onestep';
        // called the old way, with no runeword name — must not throw and must not invent a row
        return String(w._rwTipHtml(tip) || '').indexOf('att-bases') >= 0;
      })(),
    };
  });
  expect(r.onestep).toBe(true);
  // the refusals — each one a separate way the row could leak somewhere it was never asked for
  expect(r.all).toBe(false);
  expect(r.now).toBe(false);
  expect(r.completed).toBe(false);
  expect(r.otherTab).toBe(false);
  expect(r.noName).toBe(false);
});

test('(b) no tile ever names a base whose TRUSTED socket max is below what the word needs', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    const bad: string[] = [];
    let tiles = 0;
    let words = 0;
    Object.keys(w.RUNEWORD_TIP).forEach((rw: string) => {
      const need = w._rwSock ? w._rwSock(rw) : 0;
      if (!need) return;
      const html = String(w._rwHostBaseTiles(rw) || '');
      if (!html) return;
      words++;
      const d = document.createElement('div');
      d.innerHTML = html;
      Array.from(d.querySelectorAll('.att-base')).forEach((e: any) => {
        tiles++;
        const nm = (e.querySelector('.att-base-n') || {}).textContent || '';
        // _keepSocketCeil returns 0 for WEAPONS on purpose (their BASE_DB maxes are known
        // understated — v553's real 2os Wand), so weapons fail OPEN and are not judged here.
        let ceil = 0;
        try { ceil = w._keepSocketCeil ? w._keepSocketCeil(nm) || 0 : 0; } catch (x) { ceil = 0; }
        if (ceil && need > ceil) bad.push(`${rw} → ${nm} (needs ${need}, trusted max ${ceil})`);
      });
    });
    return { bad, tiles, words };
  });
  expect(r.words).toBeGreaterThan(20);   // the sweep must actually have swept something
  expect(r.tiles).toBeGreaterThan(50);
  expect(r.bad).toEqual([]);
});

test('(c) the tiles are the Forge meta-base engine, not a second list of my own', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    const out: any[] = [];
    ['Bramble', 'Wrath', 'Chains of Honor', 'Enigma', 'Insight'].forEach((rw: string) => {
      const meta = (w._forgeMetaBase(rw) || {}).names || [];
      const need = w._rwSock ? w._rwSock(rw) : 0;
      // the row is the meta list, minus only the socket-infeasible entries, capped at 4
      const expected = meta.slice(0, 4).filter((bn: string) => {
        let ceil = 0;
        try { ceil = w._keepSocketCeil ? w._keepSocketCeil(bn) || 0 : 0; } catch (x) { ceil = 0; }
        return !need || !ceil || need <= ceil;
      });
      const d = document.createElement('div');
      d.innerHTML = String(w._rwHostBaseTiles(rw) || '');
      const shown = Array.from(d.querySelectorAll('.att-base-n')).map((e: any) => e.textContent);
      out.push({ rw, expected, shown });
    });
    return out;
  });
  for (const row of r) expect(row.shown, row.rw).toEqual(row.expected);
});

// v1713 — THE CLASS GATE. A full audit (99 words x 508 bases) caught the curated meta list
// recommending four bases that cannot host their word AT ALL: Beast→Scourge and Doom→Scourge
// (maces, for words wanting Axes/Scepters/Hammers), Destruction→Berserker Axe and
// Lawbringer→Tyrant Club. Cubing Ber/Um/Mal into one of those destroys the runes. The socket
// filter could never catch it — those bases have plenty of sockets, they are the wrong CLASS.
test('(e) every tile is CLASS-LEGAL for its word — _baseRunewords is the authority', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    const illegal: string[] = [];
    let tiles = 0, words = 0, lostAll = 0;
    Object.keys(w.RUNEWORD_TIP).forEach((rw: string) => {
      const meta = ((w._forgeMetaBase(rw) || {}).names || []);
      const html = String(w._rwHostBaseTiles(rw) || '');
      if (meta.length && !html) { lostAll++; return; }
      if (!html) return;
      words++;
      const d = document.createElement('div');
      d.innerHTML = html;
      Array.from(d.querySelectorAll('.att-base-n')).forEach((e: any) => {
        tiles++;
        const nm = e.textContent || '';
        let hosts: any[] = [];
        try { hosts = w._baseRunewords(nm) || []; } catch (x) { hosts = []; }
        if (hosts.length && !hosts.some((h: any) => h.n === rw)) illegal.push(`${rw} → ${nm}`);
      });
    });
    return { illegal, tiles, words, lostAll };
  });
  expect(r.words).toBeGreaterThan(40);
  expect(r.tiles).toBeGreaterThan(80);
  expect(r.illegal).toEqual([]);      // Beast→Scourge and its three siblings must never come back
  expect(r.lostAll).toBe(0);          // and the filter must not empty a row that had names
});

// v1713 — THE FOOTNOTE MUST COUNT WHAT IT CLAIMS. It counted with _keepSocketCeil, which zeroes
// every WEAPON, so it advertised bases that cannot hold the word: 88 of 99 words overstated, 2,585
// phantom options in total. Unbending Will said "40 more" when six swords in the game reach 6os.
test('(f) the footnote counts only bases that can really hold the word', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const wrong: string[] = [];
    Object.keys(w.RUNEWORD_TIP).forEach((rw: string) => {
      const need = w._rwSock ? w._rwSock(rw) : 0;
      if (!need) return;
      // recompute independently from the raw data, then compare with what the page reports
      let truth = 0;
      Object.keys(w.BASE_DB).forEach((bn: string) => {
        let mx = 0;
        try { mx = parseInt(w._socketMaxFor(bn), 10) || 0; } catch (x) { mx = 0; }
        let hosts: any[] = [];
        try { hosts = w._baseRunewords(bn) || []; } catch (x) { hosts = []; }
        if (hosts.some((h: any) => h.n === rw) && (!mx || need <= mx)) truth++;
      });
      const got = w._rwHostCount(rw);
      if (got !== truth) wrong.push(`${rw}: reports ${got}, truth ${truth}`);
    });
    return wrong;
  });
  expect(r).toEqual([]);
});

// v1714 — reconciled against the GAME'S OWN tables (weapons/armor/runes/itemtypes.txt, pulled from
// the local CASC store). Three routing facts that no website settles, each now pinned:
//   * a necro shrunken head and a grimoire ARE shields (itemtypes: head/grim -> shld)
//   * War Fist and Battle Cestus hold 2 sockets, not 3
//   * a CLUB is not a MACE — club/mace/hamm are siblings under blun
test('(g) game-truth routing facts', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const hosts = (b: string) => (w._baseRunewords(b) || []).map((x: any) => x.n);
    return {
      // necro bases host the 2-socket shield words
      skullRhyme: hosts('Bloodlord Skull').includes('Rhyme'),
      skullSplendor: hosts('Bloodlord Skull').includes('Splendor'),
      grimRhyme: hosts('Blasphemous Grimoire').includes('Rhyme'),
      // ...but Exile is auric-only and must never reach them
      skullExile: hosts('Bloodlord Skull').includes('Exile'),
      // socket maxima, as the game states them
      warFist: parseInt(w._socketMaxFor('War Fist'), 10),
      battleCestus: parseInt(w._socketMaxFor('Battle Cestus'), 10),
      feralClaws: parseInt(w._socketMaxFor('Feral Claws'), 10),
      // a club is not a mace: Steel names types, Black names Clubs explicitly
      truncheonSteel: hosts('Truncheon').includes('Steel'),
      tyrantSteel: hosts('Tyrant Club').includes('Steel'),
      truncheonBlack: hosts('Truncheon').includes('Black'),
      // and a generic weapon word still reaches a club (blun -> mele -> weap)
      truncheonStrength: hosts('Truncheon').includes('Strength'),
    };
  });
  expect(r.skullRhyme).toBe(true);
  expect(r.skullSplendor).toBe(true);
  expect(r.grimRhyme).toBe(true);
  expect(r.skullExile).toBe(false);
  expect(r.warFist).toBe(2);
  expect(r.battleCestus).toBe(2);
  expect(r.feralClaws).toBe(3);       // the rest of the claw family is unchanged
  expect(r.truncheonSteel).toBe(false);
  expect(r.tyrantSteel).toBe(false);
  expect(r.truncheonBlack).toBe(true);
  expect(r.truncheonStrength).toBe(true);
});

// v1714 — THE OTHER END OF THE WIRE. Teaching _baseRunewords that a shrunken head is a shield is
// only half a feature: MAKE NOW is a different consumer, and between forgeScan's
// `_baseRunewords(b.base)` and its `now` bucket sit a hand gate, an endgame-gear gate and the
// socket rule — any of which can drop the base while both ends still look wired.
// So this owns a 2-socket Bloodlord Skull and asserts Rhyme is TASKED, with the runes-absent
// control asserted just as hard: a bucket that accepts everything proves nothing.
test('(h) a necro base reaches MAKE NOW, and only when the runes are actually held', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const setup = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry && w._ensureSocketBaseEntry('Bloodlord Skull (2os)');
    w.toggleOwned && w.toggleOwned('Bloodlord Skull (2os)');
    return (w._ownedBases ? w._ownedBases() : []).length;
  });
  expect(setup).toBeGreaterThan(0);
  await page.waitForTimeout(1200);

  const pick = (sc: any, key: string) =>
    (sc[key] || []).filter((t: any) => t.rw === 'Rhyme')
      .map((t: any) => ({ base: t.base && t.base.base, sub: t.sub || null }));

  // CONTROL — base in hand, runes absent: Rhyme must be ONE STEP (needs runes), never MAKE NOW.
  const before = await page.evaluate(() => {
    const w: any = window;
    w.LSR.setItem('d2r_runeStash', JSON.stringify({}));
    const sc = w.forgeScan();
    return {
      now: (sc.now || []).filter((t: any) => t.rw === 'Rhyme').length,
      onestep: (sc.onestep || []).filter((t: any) => t.rw === 'Rhyme')
        .map((t: any) => ({ base: t.base && t.base.base, sub: t.sub })),
    };
  });
  expect(before.now).toBe(0);
  expect(before.onestep.some((t: any) => t.base === 'Bloodlord Skull' && t.sub === 'runes')).toBe(true);

  // now hold the runes — Rhyme must move to MAKE NOW, naming that base
  const after = await page.evaluate(() => {
    const w: any = window;
    const s: any = {};
    (w.RUNEWORD_TIP['Rhyme'].rec || []).forEach((r: string) => { s[r] = 3; });
    w.LSR.setItem('d2r_runeStash', JSON.stringify(s));
    const sc = w.forgeScan();
    return (sc.now || []).filter((t: any) => t.rw === 'Rhyme')
      .map((t: any) => (t.base && t.base.base) || null);
  });
  expect(after).toContain('Bloodlord Skull');
});

test('(d) an unknown word yields NO row — never an empty bordered box', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    return {
      bogus: String(w._rwHostBaseTiles('Not A Runeword At All') || ''),
      empty: String(w._rwHostBaseTiles('') || ''),
      nul: String(w._rwHostBaseTiles(null) || ''),
    };
  });
  expect(r.bogus).toBe('');
  expect(r.empty).toBe('');
  expect(r.nul).toBe('');
});
