import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1621 — THE TITLE WEARS ITS RARITY, AND EACH CRAFT WEARS ITS GEM.
//
// Konyo: "now for griswald i want it green color as is the rest of the console sycned to that
// color.. and same for UNIQUES the frostburn needs the unique color. and for blood safety... they
// should be gems extracted from the game like is the forge for the caster.. they are gems relevant
// and colored".
//
// Both heroes printed the same cream-gold whatever they named, so a set piece and a unique were
// indistinguishable at the largest text on the page — while the card one hover away had them right.
// And all four FORGE QUESTS chips wore the same Hell's Forge medallion, which said "forge" four
// times and "which craft" never.
//
// Neither mapping is invented here. bible.html's CRAFTS has carried gem/gemType/color since the
// workshop was built; the BRIDGE was flattening craftTypes to a bare name and throwing the rest
// away. The rarity colours are D2's own quality palette, declared once as --rar-* and read by the
// hero title AND the hover card, so the two cannot drift.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

const CRAFTS = [
  { craft: 'Caster', gem: 'Perfect Amethyst', color: '#b48ce0', art: 'art/hd_perfect_amethyst.png' },
  { craft: 'Blood', gem: 'Perfect Ruby', color: '#e0556a', art: 'art/hd_perfect_ruby.png' },
  { craft: 'Safety', gem: 'Perfect Emerald', color: '#5fd07a', art: 'art/hd_perfect_emerald.png' },
  { craft: 'Hit Power', gem: 'Perfect Sapphire', color: '#5b8ff0', art: 'art/hd_perfect_sapphire.png' },
];

async function console_(page: any) {
  await page.addInitScript((crafts: any) => {
    localStorage.setItem('d2r_grailFarm', JSON.stringify([{ name: 'Frostburn', source: 'Hell Mephisto',
      dropChance: 0.0002, killsPerHr: 100, art: 'art/hd_gaunlets_h.png', rarity: 'unique' }]));
    localStorage.setItem('d2r_setFarm', JSON.stringify([{ name: "Griswold's Honor (Shield)",
      set: "Griswold's Legacy", left: 2, source: 'Hell TZ Pindleskin', dropChance: 0.0003,
      killsPerHr: 90, art: 'art/hd_crown_shield.png', rarity: 'set' }]));
    localStorage.setItem('d2r_forgeSummary', JSON.stringify({ ts: 1, craftTypes: crafts }));
  }, CRAFTS);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, body: '' });
  });
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) {}
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true,
      ranked: items.map((it: any, i: number) => ({ name: it.name, source: it.source, expectedHours: 1.3 + i })) }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/evrank',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);
}

test.describe('v1621 — rarity on the title, gems on the crafts', () => {
  test('★★★ the set piece is GREEN and the unique is not — they must differ', async ({ page }) => {
    await console_(page);
    const c = await page.evaluate(() => {
      const u: any = document.querySelector('#hub-hero .hh-name');
      const s: any = document.querySelector('#hub-hero-sets .hh-name');
      return { uni: u ? getComputedStyle(u).color : null, uniCls: u?.className || '',
               set: s ? getComputedStyle(s).color : null, setCls: s?.className || '' };
    });
    expect(c.setCls).toContain('r-set');
    expect(c.uniCls).toContain('r-unique');
    expect(c.set, "D2's set green").toBe('rgb(0, 255, 0)');
    expect(c.uni, "D2's unique tan — NOT the console's own gold, which is what it was").toBe('rgb(199, 179, 119)');
    expect(c.set, 'the whole point: two rarities cannot look the same').not.toBe(c.uni);
  });

  test('★★★ the title and its own hover card agree on the colour', async ({ page }) => {
    /* The reason --rar-* exists rather than a hex at each surface: before this, the card had the
       rarity right and the title did not, on the same item, two pixels apart. */
    await console_(page);
    const same = await page.evaluate(() => {
      const pick = (heroSel: string) => {
        const n: any = document.querySelector(heroSel);
        const title = getComputedStyle(n).color;
        (window as any)._itemTip.show(n); (window as any)._itemTip.move(300, 300);
        const card = getComputedStyle(document.querySelector('#itip .itip-n') as any).color;
        return { title, card };
      };
      return { set: pick('#hub-hero-sets .hh-name'), uni: pick('#hub-hero .hh-name') };
    });
    expect(same.set.card, 'set: title vs card').toBe(same.set.title);
    expect(same.uni.card, 'unique: title vs card').toBe(same.uni.title);
  });

  test('★★★ each craft chip wears ITS OWN gem, extracted from the game', async ({ page }) => {
    await console_(page);
    const chips = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#hd-forge-chips .hd-chip')).map((c: any) => ({
        text: (c.textContent || '').trim(),
        art: (c.querySelector('img') as any)?.src.split('/').pop() || null,
        loaded: !!(c.querySelector('img') as any)?.naturalWidth,
        title: c.getAttribute('title') || '',
      })));
    expect(chips.length).toBe(4);
    const want: any = { Caster: 'hd_perfect_amethyst.png', Blood: 'hd_perfect_ruby.png',
                        Safety: 'hd_perfect_emerald.png', 'Hit Power': 'hd_perfect_sapphire.png' };
    for (const c of chips) {
      const craft = Object.keys(want).find((k) => c.text.startsWith(k));
      expect(craft, `unexpected chip: ${c.text}`).toBeTruthy();
      expect(c.art, `${craft} must wear its own gem`).toBe(want[craft as string]);
      expect(c.loaded, `${craft}'s gem must actually decode`).toBe(true);
      expect(c.title, 'and say which gem the craft needs').toContain('Perfect');
    }
    // four crafts, four DIFFERENT gems — the defect was one picture used four times
    expect(new Set(chips.map((c) => c.art)).size).toBe(4);
  });

  test('★★ the four gems are all on disk (Perfect Sapphire was missing)', async () => {
    for (const g of ['amethyst', 'ruby', 'emerald', 'sapphire']) {
      const p = path.join(REPO, 'art', `hd_perfect_${g}.png`);
      expect(fs.existsSync(p), `hd_perfect_${g}.png — the Hit Power craft had no gem before this`).toBe(true);
      expect(fs.statSync(p).size).toBeGreaterThan(400);
    }
    // and it stays reproducible rather than hand-pulled
    const ex = fs.readFileSync(path.join(REPO, 'tv', 'extract_ui_icons.py'), 'utf8');
    expect(ex, 'the sapphire must be re-pullable').toContain('hd_perfect_sapphire.png');
    expect(ex, 'CASC spells it "saphire" — a real in-game filename typo').toContain('perfect_saphire.sprite');
  });

  test('★★ the BOARD still owns the craft→gem truth; the bridge only carries it', async ({ page }) => {
    /* If this ever drifts, the console would be painting a mapping the workshop disagrees with. */
    await page.goto(BOARD); await page.waitForTimeout(2400);
    const map = await page.evaluate(() => {
      const C = (window as any).CRAFTS || [];
      return C.map((c: any) => [c.key, c.gem, c.color]);
    });
    expect(map).toEqual(expect.arrayContaining([
      ['Caster', 'Perfect Amethyst', '#b48ce0'],
      ['Blood', 'Perfect Ruby', '#e0556a'],
      ['Safety', 'Perfect Emerald', '#5fd07a'],
      ['Hit Power', 'Perfect Sapphire', '#5b8ff0'],
    ]));
  });

  test('★★★ every --rar-* EQUALS the board\'s --q-* — this is what caught the wrong gold', async ({ page }) => {
    /* v1622. --rar-unique shipped as #f0c060, this console's own --gold, so the one title meant to
       announce a unique looked like every gold border around it. Konyo spotted it immediately:
       "it doesnt look so it looks like the rest of the console". The other three happened to be
       right, which is exactly how a wrong one hides — so the invariant is not "the colours look
       sensible", it is "they ARE the board's".

       v1625 extends the SAME mechanism to the two tokens this version needs: the runeword/rune
       orange the Forge tab is tinted with, and the crafted orange the CRAFTS chip moves to. No hex
       appears below — the board is read live and IS the reference, so a typo in either document
       cannot be typed identically into the assertion. */
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const board = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const g = (n: string) => cs.getPropertyValue(n).trim().toLowerCase();
      return { unique: g('--q-unique'), set: g('--q-set'), rare: g('--q-rare'), magic: g('--q-magic'),
               rune: g('--rune'), orange: g('--q-orange') };
    });
    // the reference must actually exist — a board token that resolved to '' would make the
    // comparison below pass against an equally-empty console token and prove nothing
    for (const [k, v] of Object.entries(board))
      expect(v, `board --q-${k} must be a real colour, not empty`).toMatch(/^#[0-9a-f]{3,8}$/);
    await console_(page);
    const cons = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const g = (n: string) => cs.getPropertyValue(n).trim().toLowerCase();
      return { unique: g('--rar-unique'), set: g('--rar-set'), rare: g('--rar-rare'), magic: g('--rar-magic'),
               rune: g('--rar-rune'), orange: g('--rar-orange') };
    });
    expect(cons).toEqual(board);
  });

  test('★★★ the craft GEM colours survive the purple→orange sweep untouched', async ({ page }) => {
    /* v1625. Owner A moves every CRAFT-QUALITY surface off purple onto D2's crafted orange. The
       four chips below are NOT the craft quality — they are the GEM each craft consumes (amethyst
       / ruby / emerald / sapphire), shipped in v1621, and a grep-and-replace that swept them would
       repaint four distinct crafts one colour again, which is the exact defect v1621 fixed.
       Measured as COMPUTED style, not as "the class is present" — that is the v1622 lesson. */
    // the crafted orange is taken from the BOARD, not from --rar-orange: if the console token were
    // missing this test would otherwise compare every gem against an empty string and pass blind
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const orangeHex = await page.evaluate(() => getComputedStyle(document.documentElement)
      .getPropertyValue('--q-orange').trim().toLowerCase());
    expect(orangeHex, 'the board must declare --q-orange for this guard to mean anything')
      .toMatch(/^#[0-9a-f]{3,8}$/);
    await console_(page);
    const got = await page.evaluate(() => {
      const probe = document.createElement('span');
      document.body.appendChild(probe);
      const asRgb = (hex: string) => { probe.style.color = ''; probe.style.color = hex;
        return getComputedStyle(probe).color; };
      const out = Array.from(document.querySelectorAll('#hd-forge-chips .hd-chip')).map((c: any) => {
        const cs = getComputedStyle(c);
        return { text: (c.textContent || '').trim(),
                 gemc: cs.getPropertyValue('--gemc').trim().toLowerCase(),
                 gemcRgb: asRgb(cs.getPropertyValue('--gemc').trim()),
                 color: cs.color, border: cs.borderTopColor };
      });
      probe.remove();
      return out;
    });
    expect(got.length).toBe(4);
    for (const c of CRAFTS) {
      const chip = got.find((g) => g.text.startsWith(c.craft));
      expect(chip, `${c.craft} chip missing`).toBeTruthy();
      expect(chip!.gemc, `${c.craft} must still wear its ${c.gem} — the sweep must not touch gems`)
        .toBe(c.color);
      // and the tint must actually REACH the pixels: a live colour derived from the gem, never the
      // chip's default cream (#d9c9a0) and never the crafted orange the sweep is spreading
      expect(chip!.color, `${c.craft}: the gem tint must be rendered`).not.toBe('rgb(217, 201, 160)');
    }
    // four crafts, four DIFFERENT rendered colours — one flat colour is the v1621 defect returning
    expect(new Set(got.map((g) => g.color)).size, 'the four crafts must still read as four things').toBe(4);
    // and none of the four may have become the crafted orange
    const orangeRgb = await page.evaluate((hex: string) => {
      const p = document.createElement('span'); p.style.color = hex; document.body.appendChild(p);
      const v = getComputedStyle(p).color; p.remove(); return v;
    }, orangeHex);
    for (const g of got)
      expect(g.gemcRgb, `${g.text}: swept onto the crafted orange`).not.toBe(orangeRgb);
  });

  test('★★★ the board\'s CRAFTS filter chip is D2\'s crafted ORANGE, not the old purple', async ({ page }) => {
    /* v1625. Konyo: "for crafts inpurple it can be changed to match the orange line ingame in
       diablo ii color also". The chip was #c79ce6 — a colour D2 does not use for anything, on the
       one quality D2 paints orange. Both states are measured: the resting count capsule
       (.ft-craft .ft-ct, bible.html:7393) and the lit tab (.ft-craft.on, :7401). The expected value
       is READ from --q-orange, never typed; the purple is named only as the thing it must not be. */
    await page.goto(BOARD); await page.waitForTimeout(2400);
    await page.evaluate(() => { try { (window as any).switchTab('forge'); } catch (e) {} });
    await page.waitForTimeout(1500);
    /* .forge-tab carries `transition: color .16s` (bible.html:7382). Reading getComputedStyle the
       instant after classList.add('on') returns the START frame of that transition — the resting
       #b7a888 — which is what this probe measured on its first draft and it wrongly accused the
       board of ignoring its own rule. The lit state is therefore read AFTER the transition lands. */
    const rest = await page.evaluate(() => {
      const tab: any = document.querySelector('#tab-forge .forge-tab.ft-craft');
      if (!tab) return null;
      const probe = document.createElement('span');
      probe.style.color = getComputedStyle(document.documentElement).getPropertyValue('--q-orange').trim();
      document.body.appendChild(probe);
      const orange = getComputedStyle(probe).color;
      probe.remove();
      const ct: any = tab.querySelector('.ft-ct');
      const out = { orange, ct: ct ? getComputedStyle(ct).color : null, on: tab.classList.contains('on') };
      tab.classList.add('on');           // lit state, measured after the .16s colour transition
      return out;
    });
    await page.waitForTimeout(500);
    const lit = rest ? await page.evaluate(() => {
      const tab: any = document.querySelector('#tab-forge .forge-tab.ft-craft');
      return { tab: getComputedStyle(tab).color, bd: getComputedStyle(tab).borderTopColor };
    }) : null;
    const m = rest ? { orange: rest.orange, rest: { ct: rest.ct }, lit: lit! } : null;
    expect(m, 'the Forge CRAFTS filter chip must exist to be measured').toBeTruthy();
    const PURPLE = 'rgb(199, 156, 230)';   // #c79ce6 — the colour being removed, named to be excluded
    expect(m!.rest.ct, 'resting CRAFTS count: D2 paints crafted items orange').toBe(m!.orange);
    expect(m!.rest.ct, 'and it must no longer be the invented purple').not.toBe(PURPLE);
    expect(m!.lit.tab, 'lit CRAFTS tab: same orange').toBe(m!.orange);
    expect(m!.lit.tab, 'lit CRAFTS tab must not be the invented purple').not.toBe(PURPLE);
  });
});
