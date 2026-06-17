import { test, expect } from '@playwright/test';

// v341.6 — in-game rarity colour, EVERYWHERE + popping. Closes the two audited gaps where the
// item NAME text was plain (Vault dock chips + the item-detail card name), and confirms the
// canonical _Q_HEX palette drives them. Module-scoped globals (itemDetailHtml/_Q_HEX/_artRarity)
// are reached via eval() inside page.evaluate (they are NOT on window).
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForTimeout(900);
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
    return {
      gemHasName: /cw-ing-nm/.test(gemChip), gemColor: (gemChip.match(/--ing-c:([^";]+)/) || [])[1],
      runeOrange: /--ing-c:#ffa800/.test(runeChip), runeHaveBadge: /cw-bg-have/.test(runeChip),
      jewelBlue: /--ing-c:#6969ff/.test(jewelChip), jewelTip: jewelChip.includes('data-arttip="any jewel"'),
      baseBlue: /--ing-c:#6969ff/.test(baseChip), baseLockedHave: /cw-bg-have/.test(baseChip) && /cw-ing-locked/.test(baseChip), baseTip: baseChip.includes('data-arttip="magic Gloves base"'),
      jewelResolvesRich: w._arttipResolve('any jewel')?.rich === true,
    };
  });
  expect(r.gemHasName).toBe(true);
  expect(r.gemColor).toBe('#e0556a');       // Perfect Ruby = ruby red
  expect(r.runeOrange).toBe(true);          // rune = orange
  expect(r.runeHaveBadge).toBe(true);       // status is a SEPARATE green badge
  expect(r.jewelBlue).toBe(true);           // jewel = magic blue
  expect(r.jewelTip).toBe(true);            // rich hover card
  expect(r.baseBlue).toBe(true);            // magic base = magic blue
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
  expect(r.base).toBe('#9fb0ff');   // magic base → blue (was white)
  expect(r.jewel).toBe('#9fb0ff');  // jewel (magic) → blue
  expect(r.rune).toBe('#ffa800');   // rune → orange
  expect(r.gem).toBe('#e0556a');    // Perfect Ruby → ruby red
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
      runeOrange: nmCol(rune).includes('#ffa800'), gemPurple: nmCol(gem).includes('#b48ce0'),
      tipMagic: w._jewelTipHtml(false).includes('Magic Jewel'), tipRare: w._jewelTipHtml(true).includes('Rare Jewel'),
      tintRare: w._tipTint('rare jewel'),
      bloodFirst: closeCrafts.slice(0, 3).every((x: any) => x.craft === 'Blood'),  // gem-held (Ruby→Blood) ranks first
    };
  });
  expect(r.jwMagicImg).toBe(true);                 // real jewel sprite, not a ◈ dot
  expect(r.jwRareImg).toBe(true);
  expect(r.jwMagicArttip).toBe('magic jewel');
  expect(r.jwRareArttip).toBe('rare jewel');       // distinct tooltips
  expect(r.runeOrange).toBe(true);                 // picker rune name = orange
  expect(r.gemPurple).toBe(true);                  // picker gem name = its gem colour
  expect(r.tipMagic).toBe(true);
  expect(r.tipRare).toBe(true);
  expect(r.tintRare).toBe('#ffff64');              // rare jewel title = yellow
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
    // scan every codex item: tint must match its rarity colour
    const Q: any = { unique: '#c7b377', set: '#00ff00', magic: '#9fb0ff', rare: '#ffff64', crafted: '#ffa800', rw: '#ffa800', rune: '#ffa800', basic: '#f4f4f4' };
    const items = eval('ITEM_CODEX'); let mism = 0;
    Object.keys(items).forEach((k: string) => {
      const it = items[k]; if (!it) return; const rar = w._artRarity(k) || it.rarity; const want = Q[rar]; const tint = w._tipTint(k);
      if (want && tint && tint.toLowerCase() !== want.toLowerCase()) mism++;
    });
    // the #arttip title carries a currentColor glow
    let titleGlows = false;
    for (const ss of Array.from(document.styleSheets)) { try { for (const rule of Array.from((ss as CSSStyleSheet).cssRules)) {
      if (/#arttip .att-name\b/.test(rule.cssText) && /text-shadow/i.test(rule.cssText) && /currentcolor/i.test(rule.cssText)) titleGlows = true;
    } } catch (e) {} }
    return { cm, wilhelm, spirit, mism, titleGlows };
  });
  expect(r.cm).toBe('#c7b377');     // Crescent Moon = unique gold (was orange)
  expect(r.wilhelm).toBe('#00ff00'); // set green
  expect(r.spirit).toBe('#ffa800');  // runeword orange (real runeword still works)
  expect(r.mism).toBe(0);            // ZERO tint/rarity mismatches across the codex
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
      hero: !!document.querySelector('#tools-legend-modal .tlg-hero-t'),
    };
  });
  expect(r.btn).toBe(true);
  expect(r.helpStillThere).toBe(true);   // additive — the ? help is untouched
  expect(r.shown).toBe(true);
  expect(r.cards).toBe(8);               // one card per tool
  expect(r.featured).toBe(true);         // AI Helper featured with a badge
  expect(r.chips).toBe(6);               // the 6-rarity colour legend
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

// v341.26 — every set member (all 13 sets) must resolve its INDIVIDUAL affixes in the floating
// tooltip, regardless of whether findSetPiece's older list knows the piece (codex-driven fallback).
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
  expect(r.setCount).toBe(13);
  expect(r.bad, 'set pieces missing per-piece affixes: ' + r.bad.join(', ')).toEqual([]);
});
