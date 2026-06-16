import { test, expect } from '@playwright/test';

// v331 — AI Diablo II Helper: buildAskSnapshot reads live tallies + makeable-now engines,
// the #ask-bible-card injects after the Crafting Workshop, and askBible POSTs to /api/ask.
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).buildAskSnapshot && (window as any).askBible);
  await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
});

test('buildAskSnapshot returns the makeable-now snapshot shape from live tallies', async ({ page }) => {
  const snap = await page.evaluate(() => {
    // seed a couple runes/gems so the snapshot has content
    try { (window as any).adjustRuneStash && (window as any).adjustRuneStash('Tal', 5); } catch (e) {}
    try { (window as any).adjustGemStash && (window as any).adjustGemStash('Perfect Amethyst', 2); } catch (e) {}
    return (window as any).buildAskSnapshot();
  });
  expect(snap).toHaveProperty('runewords');
  expect(snap.runewords).toHaveProperty('completableNow');
  expect(Array.isArray(snap.runewords.completableNow)).toBe(true);
  expect(snap).toHaveProperty('crafts');
  expect(Array.isArray(snap.crafts.cubeableNow)).toBe(true);
  expect(Array.isArray(snap.crafts.oneAway)).toBe(true);
  expect(snap).toHaveProperty('tally');
  expect(snap).toHaveProperty('owned');
});

test('the #ask-bible-card injects at the TOP of the Tools tab (above the Vault) with input + chips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const card = document.getElementById('ask-bible-card');
    const tools = document.getElementById('tab-tools');
    return {
      present: !!card,
      firstInTools: tools?.firstElementChild?.id === 'ask-bible-card',
      hasInput: !!document.getElementById('ask-input'),
      hasScan: !!document.querySelector('#ask-bible-card .ask-chip-scan'),
      chips: document.querySelectorAll('#ask-bible-card .ask-chip').length,
    };
  });
  expect(r.present).toBe(true);
  expect(r.firstInTools).toBe(true);   // v335: rides above the Vault
  expect(r.hasInput).toBe(true);
  expect(r.hasScan).toBe(true);        // 🎯 scan button
  expect(r.chips).toBeGreaterThanOrEqual(5);
});

test('buildTopPicks ranks top-tier makeable opportunities + scanTopPicks renders a panel', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tp = (window as any).buildTopPicks();
    (window as any).scanTopPicks({ localOnly: true });   // local render, no AI call
    return {
      shape: ['makeNow', 'afterCubing', 'close'].every((k) => Array.isArray(tp[k])),
      panel: !!document.querySelector('#ask-thread .ask-toppicks'),
      inSnapshot: !!(window as any).buildAskSnapshot().topPicks,
    };
  });
  expect(r.shape).toBe(true);
  expect(r.panel).toBe(true);
  expect(r.inSnapshot).toBe(true);
});

test('the visual Create-Now dashboard auto-renders makeable top-tier items (runewords detected)', async ({ page }) => {
  const r = await page.evaluate(() => {
    ['Tal', 'Thul', 'Ort', 'Amn'].forEach((n) => (window as any).adjustRuneStash(n, 2)); // Spirit runes
    (window as any).renderCreateNow();
    const host = document.getElementById('create-now')!;
    return {
      atTop: document.querySelector('#ask-bible-card .boss-body')?.firstElementChild?.id === 'create-now',
      hasTitle: !!host.querySelector('.cn-title'),
      tiles: host.querySelectorAll('.cn-tile').length,
      names: [...host.querySelectorAll('.cn-name')].map((e) => e.textContent || ''),
    };
  });
  expect(r.atTop).toBe(true);          // dashboard sits at the top of the card body
  expect(r.hasTitle).toBe(true);
  expect(r.tiles).toBeGreaterThan(0);
  expect(r.names.some((n) => /Spirit/.test(n))).toBe(true);  // runewords resolve via .n (bug fix)
});

test('🧪 Preview mode simulates against a sandbox — the REAL stash is never touched', async ({ page }) => {
  const r = await page.evaluate(() => {
    const realRune = (window as any).eval('runeStash');
    const before = JSON.stringify(realRune);
    (window as any).togglePreview();                       // preview ON
    ['Tal', 'Thul', 'Ort', 'Amn'].forEach((n) => (window as any).previewAdd(n, false));  // sandbox Spirit
    (window as any).renderCreateNow();
    const host = document.getElementById('create-now')!;
    const previewNames = [...host.querySelectorAll('.cn-name')].map((e) => e.textContent || '');
    const realAfterPreview = JSON.stringify((window as any).eval('runeStash'));   // must equal `before`
    const hasBar = !!host.querySelector('.cn-preview');
    (window as any).togglePreview();                       // preview OFF
    (window as any).renderCreateNow();
    const namesOff = [...host.querySelectorAll('.cn-name')].map((e) => e.textContent || '');
    return { before, realAfterPreview, sawSpirit: previewNames.some((n) => /Spirit/.test(n)), hasBar, spiritGoneOff: !namesOff.some((n) => /Spirit/.test(n)), previewNull: (window as any).previewStash === null };
  });
  expect(r.sawSpirit).toBe(true);                 // sandbox unlocked Spirit in the dashboard
  expect(r.hasBar).toBe(true);                    // the preview bar shows
  expect(r.realAfterPreview).toBe(r.before);      // ⭐ the REAL rune stash is byte-identical — untouched
  expect(r.previewNull).toBe(true);               // toggling off clears the sandbox
  expect(r.spiritGoneOff).toBe(true);             // dashboard reverts to real data
});

test('crafted items show buff RANGES (floor → godly top%) in the floating tooltip + card', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tip = (window as any)._extraTipHtml('Crafted Caster Amulet (jackpot)');
    const card = (window as any).extraItemDetailHtml('Crafted Blood Gloves (jackpot)');
    const dire = (window as any)._extraTipHtml('Dire Hand (Crafted Blood Gloves)');
    return {
      tipCraft: /att-craft/.test(tip), tipGodly: /att-godly/.test(tip), tipChase: /att-chase/.test(tip),
      tipRange: /\d+–<b class="att-godly">\d+<\/b>/.test(tip),  // a range with the top% highlighted
      cardCraft: /att-craft/.test(card), direCraft: /att-craft/.test(dire),  // named example resolves its craft
    };
  });
  expect(r.tipCraft).toBe(true);
  expect(r.tipGodly).toBe(true);
  expect(r.tipChase).toBe(true);
  expect(r.tipRange).toBe(true);    // ⭐ shows "4–10" with the 10 (godly) highlighted
  expect(r.cardCraft).toBe(true);
  expect(r.direCraft).toBe(true);
});

test('v341 HONEST base: a craft with gem+rune but no magic base is held back until the base is added (preview + live)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const findBlood = (tp: any, bucket: string) =>
      (tp[bucket] || []).find((x: any) => x.kind === 'craft' && x.craft === 'Blood' && x.slot === 'Gloves');
    // PREVIEW: sandbox a Perfect Ruby + Nef rune (the Blood-Gloves consumables) — but NO base yet
    (window as any).togglePreview();
    (window as any).previewAdd('Perfect Ruby', 'gem');
    (window as any).previewAdd('Nef', 'rune');
    const tp1 = (window as any)._previewWrap((window as any).buildTopPicks);
    const closeNoBase = findBlood(tp1, 'close');
    const makeNoBase = findBlood(tp1, 'makeNow');
    // add the magic base → now it's honestly craftable
    (window as any).previewAdd('Gloves', 'base');
    const tp2 = (window as any)._previewWrap((window as any).buildTopPicks);
    const makeWithBase = findBlood(tp2, 'makeNow');
    (window as any).togglePreview();   // off — real stash untouched
    // LIVE workshop renders a clickable base ingredient (not an auto "basic ✓")
    (window as any).switchTab && (window as any).switchTab('tools');
    const row = (window as any)._cwRecipeRow((window as any).CRAFTS.find((c: any) => c.key === 'Blood'), 'Gloves', false);
    return {
      closeNeedsBase: !!closeNoBase && /magic Gloves base/.test(closeNoBase.need || ''),
      notMakeableNoBase: !makeNoBase,
      makeableWithBase: !!makeWithBase,
      liveBaseToggle: /cw-ing-base/.test(row) && /toggleCraftBase\('Gloves'\)/.test(row) && /＋ need/.test(row),
    };
  });
  expect(r.closeNeedsBase).toBe(true);     // 🔜 "need magic Gloves base (…)"
  expect(r.notMakeableNoBase).toBe(true);  // ⛔ NOT in Make-now without the base
  expect(r.makeableWithBase).toBe(true);   // ✅ add the base → Make-now
  expect(r.liveBaseToggle).toBe(true);     // live row: base is a click-to-mark ingredient, defaults to "need"
});

test('v341.2 the preview picker is a custom ART-RICH menu (rune/gem HD icons, base glyphs) — not a text-only <select>', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    w.togglePreview(); w._pvMenuOpen = true; w.renderCreateNow();
    const host = document.getElementById('create-now')!;
    const opts = host.querySelectorAll('.cn-pv-opt');
    const find = (re: RegExp) => [...opts].find((o) => re.test(o.textContent || ''));
    w.previewAdd('Perfect Ruby', 'gem');   // add → sandbox chip should carry art
    return {
      noNativeSelect: !host.querySelector('select'),                          // the text-only dropdown is gone
      optCount: opts.length,                                                   // 33 runes + 14 gems + 9 bases
      runeImg: !!find(/Sol rune/)?.querySelector('.cn-pv-opt-art img'),
      gemImg: !!find(/Perfect Amethyst/)?.querySelector('.cn-pv-opt-art img'),
      baseGlyph: !!find(/magic Gloves base/)?.querySelector('.cn-pv-glyph'),
      chipArt: !!host.querySelector('.cn-pv-chip img'),
    };
  });
  expect(r.noNativeSelect).toBe(true);
  expect(r.optCount).toBe(56);
  expect(r.runeImg).toBe(true);    // rune HD icon in the picker
  expect(r.gemImg).toBe(true);     // gem HD icon
  expect(r.baseGlyph).toBe(true);  // base slot glyph
  expect(r.chipArt).toBe(true);    // the sandbox chip shows art too
});

test('v341.3 dashboard tiles render with in-game rarity glow + icon-chip recipes + beats line', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    ['Tal','Thul','Ort','Amn'].forEach((n) => w.adjustRuneStash(n, 2));   // → Spirit (runeword, orange)
    w.adjustGemStash('Perfect Ruby', 1); w.adjustRuneStash('Nef', 1); w.toggleCraftBase('Gloves'); // → Blood Gloves
    w.renderCreateNow();
    const host = document.getElementById('create-now')!;
    const tiles = [...host.querySelectorAll('.cn-tile')] as HTMLElement[];
    const rw = tiles.find((t) => /Spirit/.test(t.textContent || ''));
    const craft = tiles.find((t) => /Blood Gloves/.test(t.textContent || ''));
    const orange = (el: HTMLElement | undefined) => (el?.getAttribute('style') || '').includes('#ffa800');
    return {
      runewordOrange: orange(rw),                                  // runewords = orange tier
      craftOrange: orange(craft),                                  // crafts = orange tier
      runewordRuneIcons: (rw?.querySelectorAll('.cn-rc-i img').length || 0) >= 3,  // Tal+Thul+Ort+Amn icons
      craftHasGemRuneIcons: (craft?.querySelectorAll('.cn-rc-i img').length || 0) >= 2,
      craftBeats: !!craft?.querySelector('.cn-beats'),             // "⚔ beats Magefist + Frostburn"
      noTruncatedText: !/Sharkskin · Vam/.test(host.textContent || ''),  // recipe is icons, not cut-off text
    };
  });
  expect(r.runewordOrange).toBe(true);
  expect(r.craftOrange).toBe(true);
  expect(r.runewordRuneIcons).toBe(true);     // rune sequence shown as HD icons
  expect(r.craftHasGemRuneIcons).toBe(true);
  expect(r.craftBeats).toBe(true);
  expect(r.noTruncatedText).toBe(true);
});

test('v341.4 flagship hero header + chat bubbles render (orb, Sonnet badge, AI avatar)', async ({ page }) => {
  await page.route('**/api/ask', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'Make **Spirit** first.' }) }));
  const r = await page.evaluate(async () => {
    const w = window as any;
    const card = document.getElementById('ask-bible-card')!;
    const hero = {
      flagship: card.classList.contains('ask-flagship'),
      heroHeader: !!card.querySelector('.ask-hero'),
      orb: !!card.querySelector('.ask-orb'),
      sonnet: (card.querySelector('.ask-sonnet')?.textContent || '').includes('Sonnet'),
    };
    w.askBible('test');
    await new Promise((res) => setTimeout(res, 250));
    const ans = document.querySelector('#ask-thread .ask-a.ask-bubble:not(.ask-loading)');
    return { ...hero, answerHasAvatarClass: !!ans, userBubble: !!document.querySelector('#ask-thread .ask-q') };
  });
  expect(r.flagship).toBe(true);
  expect(r.heroHeader).toBe(true);
  expect(r.orb).toBe(true);
  expect(r.sonnet).toBe(true);              // ✦ Sonnet badge
  expect(r.answerHasAvatarClass).toBe(true); // AI answer gets the 🔮-avatar bubble class
  expect(r.userBubble).toBe(true);
});

test('v341.5 rich hover tooltips: golden base-options card + emphasized endgame-craft card', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    const base = w._craftBaseTipHtml('Helm');
    const resolveBase = w._arttipResolve('magic Helm base');
    const craft = w._extraTipHtml('Crafted Blood Gloves (jackpot)');
    // picker base row carries the data-arttip that triggers the rich card
    w.togglePreview(); w._pvMenuOpen = true; w.renderCreateNow();
    const baseRow = [...document.querySelectorAll('#create-now .cn-pv-opt')].find((o) => /magic Gloves base/.test(o.textContent || ''));
    return {
      baseRows: (base.match(/cbt-row/g) || []).length,          // one per craft
      baseGemIcons: (base.match(/cbt-gem/g) || []).length >= 4,  // gem art per craft row
      baseResolvesRich: resolveBase?.rich === true,
      rowArttip: baseRow?.getAttribute('data-arttip') === 'magic Gloves base',
      craftRecipe: /att-recipe/.test(craft),                     // ingredients strip
      craftIngredientsVsResult: /ingredients/.test(craft) && /result — buffs/.test(craft),  // distinguished sections
      craftGrailRoll: /att-grailroll/.test(craft),               // ⭐ 100% god-roll = grail-tier
    };
  });
  expect(r.baseRows).toBe(4);
  expect(r.baseGemIcons).toBe(true);
  expect(r.baseResolvesRich).toBe(true);
  expect(r.rowArttip).toBe(true);
  expect(r.craftRecipe).toBe(true);
  expect(r.craftIngredientsVsResult).toBe(true);  // material-in vs result-out are visually separate
  expect(r.craftGrailRoll).toBe(true);
});

test('askBible POSTs the snapshot to /api/ask and renders the answer', async ({ page }) => {
  let posted: any = null;
  await page.route('**/api/ask', (route) => {
    posted = route.request().postDataJSON();
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'You can make **Spirit** now.' }) });
  });
  await page.evaluate(() => (window as any).askBible('what can I make?'));
  await page.waitForFunction(() => /Spirit/.test(document.getElementById('ask-thread')?.textContent || ''));
  const r = await page.evaluate(() => ({
    answer: document.querySelector('#ask-thread .ask-a:not(.ask-toppicks)')?.innerHTML || '',
    q: document.querySelector('#ask-thread .ask-q')?.textContent || '',
  }));
  expect(posted).not.toBeNull();
  expect(posted.question).toBe('what can I make?');
  expect(posted).toHaveProperty('snapshot');
  expect(posted.snapshot).toHaveProperty('runewords');
  expect(r.q).toBe('what can I make?');
  expect(r.answer).toContain('<b>Spirit</b>');   // **bold** → <b> via _askMd
});
