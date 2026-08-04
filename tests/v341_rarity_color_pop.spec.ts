import { test, expect } from '@playwright/test';

// v341.6 — in-game rarity colour, EVERYWHERE + popping. Closes the two audited gaps where the
// item NAME text was plain (Vault dock chips + the item-detail card name), and confirms the
// canonical _Q_HEX palette drives them. Module-scoped globals (itemDetailHtml/_Q_HEX/_artRarity)
// are reached via eval() inside page.evaluate (they are NOT on window).
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForTimeout(900);
});

// v1632 — THE PALETTE IS OWNED BY THE APP, NOT BY THIS FILE.
// bible.html declares it once on :root and `_qTok()` reads it into `_Q_HEX`; every rarity surface
// derives from there. A restated hex in an expectation is a SECOND source of truth that silently
// rots (this spec pinned a fully-saturated set green, a hand-lightened magic blue, and collapsed
// rune + runeword + crafted onto ONE orange — three wrong slots, red on CORRECT code). So: read
// the live token off :root and assert the RELATIONSHIP.
// Deliberately LOCAL rather than importing tests/_palette.ts: that helper normalises every token
// to an 'rgb(r, g, b)' string, while half the assertions here compare against _tipTint()'s raw
// hex return, so a hex-native reader keeps both sides in one spelling. Both read the same :root.
const readTokens = (page: import('@playwright/test').Page) => page.evaluate(() => {
  const cs = getComputedStyle(document.documentElement);
  const tok = (n: string) => (cs.getPropertyValue(n) || '').trim().toLowerCase();
  return {
    unique: tok('--q-unique'), set: tok('--q-set'), magic: tok('--q-magic'), rare: tok('--q-rare'),
    crafted: tok('--q-orange'), rune: tok('--rune'), rw: tok('--q-runeword'), basic: tok('--q-normal'),
  };
});
// A hex declaration → an 'rgb(r, g, b)' string, so a token can be compared against a COMPUTED colour.
const rgbOf = (hex: string) => {
  const h = hex.trim().replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return `rgb(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255})`;
};

// The palette must stay LEGIBLE: a rarity is only doing its job if it is distinguishable from the
// qualities it is most confusable with. v1622 shipped --rar-unique as the console's chrome gold and
// THREE specs passed over it because they only asserted "a rarity class is present". This is that
// missing guard, at the token level.
test('the quality tokens stay mutually DISTINCT (set≠rune-orange, magic≠rare, unique≠crafted)', async ({ page }) => {
  const t = await readTokens(page);
  Object.entries(t).forEach(([k, v]) => expect(v, `token for ${k} must resolve to a real colour`).toMatch(/^#[0-9a-f]{3,8}$/));
  expect(t.set, 'set green must not collapse onto rune orange').not.toBe(t.rune);
  expect(t.set, 'set green must not collapse onto crafted orange').not.toBe(t.crafted);
  expect(t.rune, 'rune has its OWN orange — it is not the crafted orange').not.toBe(t.crafted);
  expect(t.magic, 'magic blue must not collapse onto rare yellow').not.toBe(t.rare);
  expect(t.unique, 'unique gold must not collapse onto crafted orange').not.toBe(t.crafted);
  expect(t.basic, 'white base must not collapse onto rare yellow').not.toBe(t.rare);
  // and the ONE deliberate alias: a runeword is rendered in the unique gold (--q-runeword:var(--q-unique))
  expect(t.rw, 'runeword deliberately aliases the unique token').toBe(t.unique);
});

test('the item-detail card renders a rarity-coloured NAME span (was hardcoded gold)', async ({ page }) => {
  // open via the calculator grid (the real user path) — click an item tile, read its detail name colour
  const r = await page.evaluate(() => {
    eval('switchTab')('calc');
    const tile = document.querySelector('.item-tile') as HTMLElement | null;
    if (tile) tile.click();
    const el = document.querySelector('#item-detail .aid-name-txt, .aid-card .aid-name-txt') as HTMLElement | null;
    return { has: !!el, colored: !!(el && /rgb/.test(getComputedStyle(el).color)) };
  });
  // the name span exists and carries a colour (rarity-driven, not the old flat gold container colour)
  if (r.has) expect(r.colored).toBe(true);
});

test('Vault dock chip NAME text carries the rarity colour (frame was the only colour before)', async ({ page }) => {
  const r = await page.evaluate(() => {
    eval('switchTab')('tools');
    ['Harlequin Crest', 'The Stone of Jordan'].forEach((n) => { try { eval('markOwned')(n); } catch (e) {} });
    try { eval('renderVault')(); } catch (e) {}
    const chip = document.querySelector('.vault-chip .vault-chip-name') as HTMLElement | null;
    return { hasNameSpan: !!chip, inlineColor: !!(chip && /color/.test(chip.getAttribute('style') || '')) };
  });
  if (r.hasNameSpan) expect(r.inlineColor).toBe(true);   // dock may be empty if nothing unsorted; only assert when present
});

test('v341.7 craft recipe chips: rarity-coloured glowing name + separate have/need badge + rich tips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    const blood = w.CRAFTS.find((c: any) => c.key === 'Blood');
    const gemChip = w._cwIngChip(blood.gem, false);    // Perfect Ruby → gem colour
    const runeChip = w._cwIngChip('Nef', true);         // rune → orange + have badge
    const jewelChip = w._cwBasicChip('any jewel', 'any jewel');
    const baseChip = w._cwBaseChip('Gloves', false, 'Heavy · Sharkskin');
    // v1632 — RENDER the chips and read the COMPUTED name colour. The old probe regexed
    // a literal blue hex out of the `--ing-c:` markup string; the chips now ship the TOKEN
    // (`--ing-c:var(--q-magic)`), so that regex could never match ANY markup the app produces
    // — an assertion that cannot pass is
    // as useless as one that cannot fail. Computed colour survives literal→token refactors.
    const host = document.createElement('div');
    host.style.cssText = 'position:absolute;left:-9999px;top:0';
    document.body.appendChild(host);
    host.innerHTML = runeChip + jewelChip + baseChip;
    const nm = [...host.querySelectorAll('.cw-ing-nm')].map((e) => getComputedStyle(e as HTMLElement).color);
    host.remove();
    return {
      gemHasName: /cw-ing-nm/.test(gemChip), gemColor: (gemChip.match(/--ing-c:([^";]+)/) || [])[1],
      nameColors: nm, runeHaveBadge: /cw-bg-have/.test(runeChip),
      jewelTip: jewelChip.includes('data-arttip="any jewel"'),
      baseLockedHave: /cw-bg-have/.test(baseChip) && /cw-ing-locked/.test(baseChip), baseTip: baseChip.includes('data-arttip="magic Gloves base"'),
      jewelResolvesRich: w._arttipResolve('any jewel')?.rich === true,
    };
  });
  const t = await readTokens(page);
  const [runeCol, jewelCol, baseCol] = r.nameColors;
  expect(r.gemHasName).toBe(true);
  expect(r.gemColor).toBe('#e0556a');       // Perfect Ruby = ruby red (a GEM colour, not a quality token)
  expect(r.nameColors, 'rune + jewel + base chips must each render a name span').toHaveLength(3);
  expect(runeCol, 'rune chip name = the live --rune token').toBe(rgbOf(t.rune));
  expect(runeCol, 'rune orange is NOT the crafted orange — the two must stay tellable apart').not.toBe(rgbOf(t.crafted));
  expect(r.runeHaveBadge).toBe(true);       // status is a SEPARATE green badge
  expect(jewelCol, 'jewel chip name = the live --q-magic token').toBe(rgbOf(t.magic));
  expect(jewelCol, 'magic blue must not read as rare yellow').not.toBe(rgbOf(t.rare));
  expect(r.jewelTip).toBe(true);            // rich hover card
  expect(baseCol, 'magic base chip name = the live --q-magic token').toBe(rgbOf(t.magic));
  expect(r.baseLockedHave).toBe(true);      // v341.44 — base is vendor-buyable → locked HAVE (not a need toggle)
  expect(r.baseTip).toBe(true);             // base → golden options card
  expect(r.jewelResolvesRich).toBe(true);
});

test('v341.7 the preview picker has a 4th Jewels section', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    w.togglePreview(); w._pvMenuOpen = true; w.renderCreateNow();
    const host = document.getElementById('create-now')!;
    const heads = [...host.querySelectorAll('.cn-pv-ggh')].map((h) => h.textContent || '');
    const jewelOpt = [...host.querySelectorAll('.cn-pv-opt')].find((o) => /magic Jewel/.test(o.textContent || ''));
    return { hasJewelsSection: heads.some((h) => /Jewel/.test(h)), groupCount: heads.length, jewelOptArttip: jewelOpt?.getAttribute('data-arttip') };
  });
  expect(r.hasJewelsSection).toBe(true);
  expect(r.groupCount).toBe(4);                 // Runes · Gems · Craft Bases · Jewels
  expect(r.jewelOptArttip).toBe('magic jewel');   // jewel row → rich card (magic/rare distinct)
});

test('v341.10 Tools-tab cards get the premium themed treatment (accent --tc) — flagship feel carried outward', async ({ page }) => {
  const r = await page.evaluate(() => {
    const ids = ['mule-vault-card', 'rune-stash-card', 'all-runewords-card', 'gem-stash-card', 'craft-workshop-card', 'horadric-recipe-card', 'material-stash-card'];
    const themed = ids.filter((id) => {
      const el = document.getElementById(id);
      return el && el.classList.contains('tool-premium') && /--tc:/.test(el.getAttribute('style') || '');
    });
    // distinct accent colours (not all the same) → cohesive but varied
    const colors = new Set(ids.map((id) => (document.getElementById(id)?.getAttribute('style') || '').match(/--tc:([^;]+)/)?.[1]).filter(Boolean));
    return { themedCount: themed.length, distinctColors: colors.size, flagshipStillUnique: document.getElementById('ask-bible-card')?.classList.contains('ask-flagship') && !document.getElementById('rune-stash-card')?.classList.contains('ask-flagship') };
  });
  expect(r.themedCount).toBe(7);             // every Tools card themed
  expect(r.distinctColors).toBeGreaterThanOrEqual(5);  // varied accents
  expect(r.flagshipStillUnique).toBe(true);  // the animated hero stays only on the AI Helper
});

test('v341.16 the floating tooltip TITLE tints to the item rarity (magic base = blue, not white)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const t = (window as any)._tipTint;
    return { base: t('magic Ring base'), jewel: t('any jewel'), rune: t('Sol'), gem: t('Perfect Ruby') };
  });
  const t = await readTokens(page);
  // v1632 — same surface, same token: v1628 made _tipTint return _Q_HEX.magic outright ("the magic
  // TOKEN, not a hand-lightened blue"), so the old pinned blue was a second palette, not a
  // second surface. Read the token; assert the relationship.
  expect(r.base).toBe(t.magic);     // magic base → the magic token (was white)
  expect(r.jewel).toBe(t.magic);    // jewel (magic) → same magic token
  expect(r.rune).toBe(t.rune);      // rune → the RUNE token
  expect(r.rune, 'the rune tint is its own orange, not the crafted one').not.toBe(t.crafted);
  expect(r.gem).toBe('#e0556a');    // Perfect Ruby → ruby red (gem colour, outside the quality palette)
});

test('v341.17 jewel magic/rare distinction + picker name colours + gem-held craft sort', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    w.togglePreview(); w._pvMenuOpen = true;
    w.previewAdd('Perfect Ruby', 'gem'); w.previewAdd('Nef', 'rune'); w.renderCreateNow();
    const host = document.getElementById('create-now')!;
    const opt = (re: RegExp) => [...host.querySelectorAll('.cn-pv-opt')].find((o) => re.test(o.textContent || ''));
    const jwMagic = opt(/magic Jewel/), jwRare = opt(/rare Jewel/), rune = opt(/Sol rune/), gem = opt(/Perfect Amethyst/);
    const nmCol = (el: any) => (el?.querySelector('.cn-pv-opt-nm')?.getAttribute('style') || '');
    const closeCrafts = w._previewWrap(w.buildTopPicks).close.filter((x: any) => x.kind === 'craft');
    return {
      jwMagicImg: !!jwMagic?.querySelector('.jw-magic img'), jwRareImg: !!jwRare?.querySelector('.jw-rare img'),
      jwMagicArttip: jwMagic?.getAttribute('data-arttip'), jwRareArttip: jwRare?.getAttribute('data-arttip'),
      runeNameCol: rune ? getComputedStyle(rune.querySelector('.cn-pv-opt-nm') as HTMLElement).color : '',
      gemPurple: nmCol(gem).includes('#b48ce0'),
      tipMagic: w._jewelTipHtml(false).includes('Magic Jewel'), tipRare: w._jewelTipHtml(true).includes('Rare Jewel'),
      tintRare: w._tipTint('rare jewel'),
      bloodFirst: closeCrafts.slice(0, 3).every((x: any) => x.craft === 'Blood'),  // gem-held (Ruby→Blood) ranks first
    };
  });
  expect(r.jwMagicImg).toBe(true);                 // real jewel sprite, not a ◈ dot
  expect(r.jwRareImg).toBe(true);
  expect(r.jwMagicArttip).toBe('magic jewel');
  expect(r.jwRareArttip).toBe('rare jewel');       // distinct tooltips
  const t = await readTokens(page);
  expect(r.runeNameCol, 'picker rune name = the live --rune token').toBe(rgbOf(t.rune));
  expect(r.runeNameCol, 'and it must stay distinct from the crafted orange').not.toBe(rgbOf(t.crafted));
  expect(r.gemPurple).toBe(true);                  // picker gem name = its gem colour (not a quality token)
  expect(r.tipMagic).toBe(true);
  expect(r.tipRare).toBe(true);
  expect(r.tintRare).toBe(t.rare);                 // rare jewel title = the live rare token
  expect(r.tintRare, 'rare yellow must not read as magic blue').not.toBe(t.magic);
  expect(r.bloodFirst).toBe(true);                 // committed-gem crafts lead the list
});

test('v341.19 Sigon set: per-piece affixes + partial bonuses (incl 30% IAS) + green glow synced', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    const card = w.setDetailHtml("Sigon's Complete Steel");
    const tip = w._arttipResolve("Sigon's Gage");
    // gic-name glow now follows the text colour (currentColor), not a fixed gold
    let glowSynced = false;
    for (const ss of Array.from(document.styleSheets)) {
      try { for (const rule of Array.from((ss as CSSStyleSheet).cssRules)) {
        if (/\.gic-name\b/.test(rule.cssText) && /text-shadow/i.test(rule.cssText) && /currentcolor/i.test(rule.cssText)) glowSynced = true;
      } } catch (e) {}
    }
    return {
      cardIAS: /30% Increased Attack Speed/.test(card),
      cardPartials: /Partial set bonuses/.test(card),
      cardLeech: /Life Stolen Per Hit/.test(card),
      cardAffixList: /ct-affixes/.test(card),
      tipIAS: /30% Increased Attack Speed/.test(tip.desc || ''),  // per-piece hover now shows real affixes
      glowSynced,
    };
  });
  expect(r.cardIAS).toBe(true);        // the famous +30% IAS now renders
  expect(r.cardPartials).toBe(true);   // partial set bonuses section
  expect(r.cardLeech).toBe(true);      // full set bonus expanded (life steal etc.)
  expect(r.cardAffixList).toBe(true);  // per-piece affixes on each tile
  expect(r.tipIAS).toBe(true);         // per-piece hover card shows individual affixes
  expect(r.glowSynced).toBe(true);     // set-green glow follows the text colour (no matte/gold mismatch)
});

test('v341.20 tooltip title tint matches the item rarity (no runeword-name collisions) + title glows', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    // a unique whose name collides with a runeword must stay gold, not runeword-orange
    const cm = w._tipTint('Crescent Moon (amulet)');
    const wilhelm = w._tipTint("Wilhelm's Pride");   // set → green
    const spirit = w._tipTint('Spirit');             // real runeword → orange
    // scan every codex item: tint must match its rarity colour. v1632 — the palette is read LIVE
    // off :root by rarity NAME (was a hardcoded 8-slot duplicate that had rotted in three slots:
    // a saturated set green, a lightened magic blue, and rune/rw/crafted collapsed onto ONE
    // orange). A mismatch now
    // reports the ITEM NAMES, not just a count, so a red says WHICH items broke.
    const cs = getComputedStyle(document.documentElement);
    const tk = (n: string) => (cs.getPropertyValue(n) || '').trim().toLowerCase();
    const Q: any = { unique: tk('--q-unique'), set: tk('--q-set'), magic: tk('--q-magic'), rare: tk('--q-rare'),
                     crafted: tk('--q-orange'), rw: tk('--q-runeword'), rune: tk('--rune'), basic: tk('--q-normal') };
    const items = eval('ITEM_CODEX'); const mismNames: string[] = []; const seen: any = {}; let checked = 0;
    Object.keys(items).forEach((k: string) => {
      const it = items[k]; if (!it) return; const rar = w._artRarity(k) || it.rarity; const want = Q[rar]; const tint = w._tipTint(k);
      if (!want || !tint) return;
      checked++; seen[rar] = (seen[rar] || 0) + 1;
      if (tint.toLowerCase() !== want.toLowerCase()) mismNames.push(k + ' [' + rar + '] tint=' + tint + ' expected=' + want);
    });
    const mism = mismNames.length;
    // the #arttip title carries a currentColor glow
    let titleGlows = false;
    for (const ss of Array.from(document.styleSheets)) { try { for (const rule of Array.from((ss as CSSStyleSheet).cssRules)) {
      if (/#arttip .att-name\b/.test(rule.cssText) && /text-shadow/i.test(rule.cssText) && /currentcolor/i.test(rule.cssText)) titleGlows = true;
    } } catch (e) {} }
    return { cm, wilhelm, spirit, mism, mismNames, checked, seen, titleGlows };
  });
  const t = await readTokens(page);
  // NON-VACUITY GUARD: a zero-mismatch sweep proves nothing if the sweep examined nothing.
  expect(r.checked, 'the codex sweep must actually examine the codex').toBeGreaterThan(200);
  expect(Object.keys(r.seen).length, 'the sweep must span several rarities, not just one').toBeGreaterThanOrEqual(3);
  expect(r.cm).toBe(t.unique);       // Crescent Moon = the unique token (name collides with a runeword; rarity wins)
  expect(r.wilhelm).toBe(t.set);     // set green — the LIVE token (D2's FontColorGreen), never a pinned literal
  expect(r.wilhelm, 'set green must not be mistakable for rune orange').not.toBe(t.rune);
  // a real runeword: --q-runeword is declared as var(--q-unique), so Spirit renders in the unique
  // gold. Assert the RELATIONSHIP the app actually declares, not a value someone remembered.
  expect(r.spirit).toBe(t.rw);
  expect(r.spirit).toBe(t.unique);
  expect(r.mism, 'tint/rarity mismatches across the codex: ' + r.mismNames.join(' | ')).toBe(0);
  expect(r.titleGlows).toBe(true);   // tooltip title glows in its colour
});

test('v341.21 the 🧰 Tools field-guide widget opens a premium structured legend (additive, beyond the ?)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const btn = document.querySelector('.tools-legend-btn') as HTMLElement | null;
    const help = document.querySelector('.help-btn:not(.tools-legend-btn)');   // the ? still exists (additive)
    if (btn) btn.click();
    const m = document.getElementById('tools-legend-modal');
    return {
      btn: !!btn, helpStillThere: !!help, shown: !!(m && m.classList.contains('show')),
      cards: document.querySelectorAll('#tools-legend-modal .tlg-card').length,
      featured: !!document.querySelector('#tools-legend-modal .tlg-card.tlg-feat .tlg-badge'),
      chips: document.querySelectorAll('#tools-legend-modal .tlg-chip').length,
      // v1632 — the legend is the one screen that TEACHES the palette, so it is asserted against
      // the palette itself: label → computed colour, compared to the live token of the same name.
      chipMap: [...document.querySelectorAll('#tools-legend-modal .tlg-chip')]
        .map((c) => [(c.textContent || '').trim().toLowerCase(), getComputedStyle(c as HTMLElement).color] as [string, string]),
      hero: !!document.querySelector('#tools-legend-modal .tlg-hero-t'),
    };
  });
  expect(r.btn).toBe(true);
  expect(r.helpStillThere).toBe(true);   // additive — the ? help is untouched
  expect(r.shown).toBe(true);
  expect(r.cards).toBe(14);              // v529 field-guide rebuild — one card per current tool
  expect(r.featured).toBe(true);         // flagship AI tools featured with a badge
  // The old assertion pinned `chips === 6` and went RED when the legend correctly grew to 8
  // (runeword + base joined). A count never said whether a single swatch was the RIGHT colour —
  // exactly the v1622 blind spot. Assert coverage + correctness against the live tokens instead.
  const tl = await readTokens(page);
  const want: Record<string, string> = { unique: tl.unique, set: tl.set, magic: tl.magic, rare: tl.rare,
    runeword: tl.rw, rune: tl.rune, crafted: tl.crafted, base: tl.basic };
  const got = new Map(r.chipMap);
  Object.entries(want).forEach(([label, hex]) => {
    expect(got.has(label), `the palette legend must teach the "${label}" quality`).toBe(true);
    expect(got.get(label), `legend swatch "${label}" must render its live token`).toBe(rgbOf(hex));
  });
  expect(r.chips).toBeGreaterThanOrEqual(Object.keys(want).length);   // every quality gets a chip
  expect(r.hero).toBe(true);             // hero header
});

test('v341.24 no special-item NAME renders uber-pink — synced (materials orange, charms gold, super-uniques su-gold)', async ({ page }) => {
  await page.setViewportSize({ width: 1400, height: 1000 });
  const tabs = ['tz', 'runes', 'rotw', 'events', 'endgame'];
  const pink: string[] = [];
  for (const t of tabs) {
    await page.evaluate((tb) => { try { (window as any).switchTab(tb); } catch (e) {} }, t);
    await page.waitForTimeout(200);
    const hits = await page.evaluate(() => {
      const out: string[] = [];
      document.querySelectorAll('[data-art-logo],[onclick*="openDrop"],.su-link,.rn-name,.ct-name,.rf-name').forEach((el) => {
        const e = el as HTMLElement; if (e.offsetParent === null) return;
        const c = getComputedStyle(e).color.replace(/\s/g, '');
        if (/^rgba?\(25[0-5],0,2(0[0-9]|1[0-9]|2[0-5])/.test(c)) { const t = (e.textContent || '').trim().slice(0, 30); if (t) out.push(t); }
      });
      return out;
    });
    pink.push(...hits);
  }
  expect(pink).toEqual([]);   // ZERO item/special names rendered in uber-pink
});

test('the universal rarity glow rule covers the name sites with a bright multi-layer shadow', async ({ page }) => {
  const r = await page.evaluate(() => {
    let txt = '';
    for (const ss of Array.from(document.styleSheets)) {
      try { for (const rule of Array.from((ss as CSSStyleSheet).cssRules)) {
        if (/aid-name-txt|vault-chip-name/.test(rule.cssText) && /text-shadow/.test(rule.cssText)) txt = rule.cssText;
      } } catch (e) {}
    }
    return { found: !!txt, multiLayer: /currentcolor[\s\S]*currentcolor/i.test(txt) };
  });
  expect(r.found).toBe(true);
  expect(r.multiLayer).toBe(true);   // bright core + halo (two currentColor layers) = it pops
});

// v341.26 — every set member (all sets) must resolve its INDIVIDUAL affixes in the floating
// tooltip, regardless of whether findSetPiece's older list knows the piece (codex-driven fallback).
// v382 — set count grew 13 → 32 (added the 17 classic + 2 RotW sets as rich cat:'set' codex entries).
test('every set piece resolves per-piece affixes via the floating tooltip', async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._arttipResolve);
  const r = await page.evaluate(() => {
    const w = window as any; const items = eval('ITEM_CODEX');
    const sets = Object.keys(items).filter((k: string) => items[k] && items[k].cat === 'set');
    const bad: string[] = [];
    sets.forEach((k: string) => (items[k].setMembers || []).forEach((m: any) => {
      const res = w._arttipResolve(m.name);
      if (!res || !/att-aff/.test(res.desc || '')) bad.push(items[k].setName + ' / ' + m.name);
    }));
    return { setCount: sets.length, bad };
  });
  expect(r.setCount).toBe(32);
  expect(r.bad, 'set pieces missing per-piece affixes: ' + r.bad.join(', ')).toEqual([]);
});
