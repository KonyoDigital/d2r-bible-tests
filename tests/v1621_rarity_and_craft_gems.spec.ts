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
       sensible", it is "they ARE the board's". */
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const board = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const g = (n: string) => cs.getPropertyValue(n).trim().toLowerCase();
      return { unique: g('--q-unique'), set: g('--q-set'), rare: g('--q-rare'), magic: g('--q-magic') };
    });
    await console_(page);
    const cons = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const g = (n: string) => cs.getPropertyValue(n).trim().toLowerCase();
      return { unique: g('--rar-unique'), set: g('--rar-set'), rare: g('--rar-rare'), magic: g('--rar-magic') };
    });
    expect(cons).toEqual(board);
  });
});
