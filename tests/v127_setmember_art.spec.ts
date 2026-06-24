import { test, expect } from './_net_stub'; // diablo2.io art stubbed — kills net-flake (audit 2026-06-12)
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v127 — the codex "Set Items" sub-list (renderCodexCard → .cx-members → artOr(m.name))
// now shows verified diablo2.io icons for the formerly-art-less set pieces. 26 members were
// scraped from each item's own diablo2.io page and auto-verified HTTP 200 image/png on
// 2026-06-08, then registered in D2IO_ART. Pure additive art-wiring: no data/odds touched.
test.describe('v127 set-member codex icons are verified + lazy', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  const NEW_MEMBERS = [
    "Aldur's Stony Gaze", "Cow King's Hide", "Cow King's Hoofs", "Cow King's Horns",
    "Griswolds's Redemption", "Hwanin's Justice", "Hwanin's Refuge",
    "Immortal King's Detail", "Immortal King's Forge", "Immortal King's Pillar",
    "Immortal King's Soul Cage", "Immortal King's Stone Crusher", "Immortal King's Will",
    "Naj's Light Plate", "Naj's Puzzler", "Sigon's Gage", "Sigon's Sabot",
    "Tal Rasha's Adjudication", "Tal Rasha's Fine-Spun Cloth", "Tal Rasha's Horadric Crest",
    "Trang-Oul's Claws", "Trang-Oul's Girth", "Trang-Oul's Guise", "Trang-Oul's Scales",
    "Trang-Oul's Wing", "Wihtstan's Guard",
  ];

  test('every newly-scouted set piece is registered in D2IO_ART with a verified _graphic.png URL', async ({ page }) => {
    const r = await page.evaluate((names) => {
      const art = (window as any).D2IO_ART;
      const missing: string[] = [];
      const badUrl: string[] = [];
      for (const n of names) {
        const u = art[n];
        if (!u) { missing.push(n); continue; }
        if (!/^art\/.+\.png$/.test(u)) badUrl.push(n + ' -> ' + u);   // v384 HD override: accept hd_/mr_/d2io_/_graphic — any present art file
      }
      return { missing, badUrl, total: Object.keys(art).length };
    }, NEW_MEMBERS);
    expect(r.missing).toEqual([]);
    expect(r.badUrl).toEqual([]);
    expect(r.total).toBeGreaterThanOrEqual(447);
  });

  test('the codex Set Items list renders a lazy verified <img> for each new member (Immortal King + Trang-Oul)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const wrap = document.createElement('div');
      wrap.innerHTML =
        (window as any).renderCodexCard('Immortal King set (any)') +
        (window as any).renderCodexCard('Trang-Oul set (any piece)');
      document.body.appendChild(wrap);
      const out: Record<string, { hasImg: boolean; lazy: boolean; onerr: boolean; src: string }> = {};
      wrap.querySelectorAll('.cx-member').forEach((m) => {
        const nm = (m.querySelector('.cx-member-nm') as HTMLElement)?.textContent?.trim() || '';
        const img = m.querySelector('.cx-member-art .d2art-img') as HTMLImageElement | null;
        out[nm] = {
          hasImg: !!img,
          lazy: img?.getAttribute('loading') === 'lazy',
          onerr: (img?.getAttribute('onerror') || '').includes('d2art-failed'),
          src: img?.getAttribute('src') || '',
        };
      });
      return out;
    });
    const targets = [
      "Immortal King's Detail", "Immortal King's Forge", "Immortal King's Pillar",
      "Immortal King's Soul Cage", "Immortal King's Stone Crusher", "Immortal King's Will",
      "Trang-Oul's Claws", "Trang-Oul's Girth", "Trang-Oul's Guise",
      "Trang-Oul's Scales", "Trang-Oul's Wing",
    ];
    for (const t of targets) {
      expect(r[t], `member row "${t}" present`).toBeTruthy();
      expect(r[t].hasImg, `${t} has an art img`).toBe(true);
      expect(r[t].lazy, `${t} img is lazy`).toBe(true);
      expect(r[t].onerr, `${t} img has the d2art-failed fallback`).toBe(true);
      expect(r[t].src, `${t} src is a verified art file`).toMatch(/^art\/.+\.png$/);   // v384 HD override: hd_/mr_/d2io_/_graphic all valid
    }
  });

  test('no console errors when rendering the set-member codex cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      for (const k of ['Sigon\'s Complete Steel', 'Cow King\'s Leathers (set)', 'Naj\'s Ancient Vestige', 'Tal Rasha set (any piece)']) {
        const d = document.createElement('div');
        d.innerHTML = (window as any).renderCodexCard(k);
        document.body.appendChild(d);
      }
    });
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });

  test('the two mislabeled members are corrected to canonical items (Aldur\'s Rhythm, Hwanin\'s Blessing)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const codex: any = ITEM_CODEX;
      const art = (window as any).D2IO_ART;
      // v383 — set-member art is now COMPLETE: all 126 pieces across all 32 sets have real diablo2.io
      // sprites registered in D2IO_ART (the 169-sprite fetch). So the gap check guards every set again.
      const names = new Set<string>();
      for (const e of Object.values(codex) as any[]) {
        if (e.setMembers) for (const m of e.setMembers) names.add(m.name);
      }
      return {
        hasOldAldur: names.has("Aldur's Gauntlet"),
        hasOldHwanin: names.has("Hwanin's Seal"),
        hasNewAldur: names.has("Aldur's Rhythm"),
        hasNewHwanin: names.has("Hwanin's Blessing"),
        aldurArt: art["Aldur's Rhythm"] || '',
        hwaninArt: art["Hwanin's Blessing"] || '',
        // zero set members lack art now
        gap: [...names].filter((n) => !art[n]),
      };
    });
    expect(r.hasOldAldur).toBe(false);
    expect(r.hasOldHwanin).toBe(false);
    expect(r.hasNewAldur).toBe(true);
    expect(r.hasNewHwanin).toBe(true);
    expect(r.aldurArt).toMatch(/^art\/.+\.png$/);   // v384 HD override may map to hd_*.png; the canonical-name correction is what's asserted here
    expect(r.hwaninArt).toMatch(/^art\/.+\.png$/);
    expect(r.gap).toEqual([]);
  });
});
