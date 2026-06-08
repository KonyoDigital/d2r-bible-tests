import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v119 — the "🟠 Super-Unique Bosses" bind table (#binds-superunique) used to be a
// flat list of 22 non-clickable names. Every row is now a clickable golden bind ID
// card (BIND_SU data → bindSUDetailHtml), transcribed VERBATIM from the verified-3.2
// table + the pack-size / field-guide rows already on the page (no new sourcing). The
// 8 rows that also own a full TZ-tab SUPER_UNIQUES card carry a cross-link to it; the
// 14 Council / Throne-wave bosses that had no card now get their own honest bind card.
// Plus: the Smith/Lister/Hephasto aura cells carry the live aura gif, and the Lister
// row now spells out the dual-layer aura (fixed Meditation + rolled Aura Enchanted).
test.describe('v119 bind super-unique ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('binds'));
    await page.waitForTimeout(150);
  });

  test('BIND_SU data + renderer helpers are exposed (22 entries)', async ({ page }) => {
    const r = await page.evaluate(() => ({
      len: ((window as any).BIND_SU || []).length,
      hasRender: typeof (window as any).bindSUDetailHtml === 'function',
      hasToggle: typeof (window as any).toggleBindSU === 'function',
      hasByName: typeof (window as any).openBindSUByName === 'function',
    }));
    expect(r.len).toBe(22);
    expect(r.hasRender).toBe(true);
    expect(r.hasToggle).toBe(true);
    expect(r.hasByName).toBe(true);
  });

  test('every bind table row is a clickable su-link routing to openBindSUByName', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-superunique');
      const links = sec ? Array.from(sec.querySelectorAll('tbody tr td.item-name .su-link')) : [];
      return {
        rows: sec ? sec.querySelectorAll('tbody tr').length : 0,
        links: links.length,
        allByName: links.every((l) => (l.getAttribute('onclick') || '').includes('openBindSUByName(')),
      };
    });
    expect(r.rows).toBe(22);
    expect(r.links).toBe(22);
    expect(r.allByName).toBe(true);
  });

  test('clicking a Council boss (no prior card) opens its honest bind ID card', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindSUByName('Toorc Icefist'));
    await page.waitForTimeout(120);
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail');
      const txt = box ? (box.textContent || '') : '';
      return {
        open: box ? !box.hasAttribute('hidden') : false,
        name: txt.includes('Toorc Icefist'),
        consume: txt.includes('Cold Res + Max') && txt.includes('-% Enemy Cold Res'),
        council: txt.includes('coded') && txt.includes('Demon'),
        tier: txt.includes('20 hard points'),
        hasGbc: !!(box && box.querySelector('.gbc-card')),
      };
    });
    expect(r.open).toBe(true);
    expect(r.name).toBe(true);
    expect(r.consume).toBe(true);
    expect(r.council).toBe(true);
    expect(r.tier).toBe(true);
    expect(r.hasGbc).toBe(true);
  });

  test('a fully-sourced boss card cross-links to its full TZ SUPER_UNIQUES card', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindSUByName('The Smith'));
    await page.waitForTimeout(120);
    const html = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail');
      return box ? box.innerHTML : '';
    });
    expect(html).toContain("jumpToSuperUniqueByName('The Smith')");
    expect(html).toContain('Holy Fire');
  });

  test('toggle is an accordion — opening a second card replaces the first; re-click closes', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindSUByName('Bartuc the Bloody'));
    await page.waitForTimeout(80);
    let t = await page.evaluate(() => (document.getElementById('bindsu-detail')!.textContent || ''));
    expect(t).toContain('Bartuc the Bloody');
    await page.evaluate(() => (window as any).openBindSUByName('Lister the Tormentor'));
    await page.waitForTimeout(80);
    t = await page.evaluate(() => (document.getElementById('bindsu-detail')!.textContent || ''));
    expect(t).toContain('Lister the Tormentor');
    expect(t).not.toContain('Bartuc the Bloody');
    // re-click same one closes it
    await page.evaluate(() => (window as any).openBindSUByName('Lister the Tormentor'));
    await page.waitForTimeout(80);
    const hidden = await page.evaluate(() => document.getElementById('bindsu-detail')!.hasAttribute('hidden'));
    expect(hidden).toBe(true);
  });

  test('the Smith / Lister / Hephasto aura cells carry a live aura gif', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-superunique');
      const cells = sec ? Array.from(sec.querySelectorAll('td[data-aura-logo]')) : [];
      const names = cells.map((c) => c.getAttribute('data-aura-logo')).sort();
      const allDecorated = cells.every((c) => c.querySelector('.aura-logo img.d2art-img'));
      return { count: cells.length, names, allDecorated };
    });
    expect(r.count).toBe(3);
    expect(r.names).toEqual(['Fanaticism', 'Holy Fire', 'Meditation']);
    expect(r.allDecorated).toBe(true);
  });

  test('Lister row spells out the dual-layer aura (fixed Meditation + rolled Aura Enchanted)', async ({ page }) => {
    const txt = await page.evaluate(() => {
      const sec = document.getElementById('binds-superunique');
      return sec ? (sec.textContent || '') : '';
    });
    expect(txt).toContain('Lvl 15 Meditation');
    expect(txt).toMatch(/rolls Aura Enchanted/);
    expect(txt).toMatch(/reroll Fanaticism/);
  });

  test('mlvl reconciliation: every carded boss agrees with its SUPER_UNIQUES entry (single source of truth)', async ({ page }) => {
    // SUPER_UNIQUES is the audited canon (v83 area+3 rule); the binds table used to carry
    // its own drifted mlvl column. Lock BIND_SU.mlvl == SUPER_UNIQUES.mlvl for every linked
    // boss AND that the static table cell shows the same number.
    const drift = await page.evaluate(() => {
      const SU = SUPER_UNIQUES as any[];
      const BS = (window as any).BIND_SU as any[];
      const sec = document.getElementById('binds-superunique');
      const out: string[] = [];
      BS.filter((b) => b.suName).forEach((b) => {
        const su = SU.find((s) => s.name === b.suName);
        if (!su) { out.push(`${b.name}: suName "${b.suName}" not in SUPER_UNIQUES`); return; }
        if (su.mlvl !== b.mlvl) out.push(`${b.name}: BIND_SU mlvl ${b.mlvl} != SUPER_UNIQUES ${su.mlvl}`);
        // the static table row's mlvl cell (3rd td) must match too
        const row = sec ? Array.from(sec.querySelectorAll('tbody tr')).find((tr) => (tr.textContent || '').includes(b.name)) : null;
        const cell = row ? (row.querySelectorAll('td')[2]?.textContent || '').trim() : '';
        if (cell !== String(su.mlvl)) out.push(`${b.name}: table cell "${cell}" != SUPER_UNIQUES ${su.mlvl}`);
      });
      return out;
    });
    expect(drift, `binds-tab mlvl drifted from SUPER_UNIQUES:\n${drift.join('\n')}`).toEqual([]);
  });

  test('council bind cards carry the enriched who + bind-tactic detail (v120)', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindSUByName('Toorc Icefist'));
    await page.waitForTimeout(120);
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail');
      const txt = box ? (box.textContent || '') : '';
      return {
        whoLabel: txt.toLowerCase().includes('who'),
        who: txt.includes('Travincal High Council'),
        tacticLabel: txt.toLowerCase().includes('bind tactic'),
        tactic: txt.includes('drop Toorc below the HP cap'),
      };
    });
    expect(r.whoLabel).toBe(true);
    expect(r.who).toBe(true);
    expect(r.tacticLabel).toBe(true);
    expect(r.tactic).toBe(true);
  });

  test('the new Council roster section lists all 6 council members + Bartuc as routable su-links (v120)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-council');
      const links = sec ? Array.from(sec.querySelectorAll('.su-link')) : [];
      const onclicks = links.map((l) => l.getAttribute('onclick') || '');
      const need = ['Ismail Vilehand', 'Geleb Flamefinger', 'Toorc Icefist',
        'Bremm Sparkfist', 'Wyand Voidbringer', 'Maffer Dragonhand', 'Bartuc the Bloody'];
      return {
        exists: !!sec,
        isSection: !!(sec && sec.querySelector('.sec-h.tier-header .sec-chev')),
        count: links.length,
        allRouted: need.every((n) => onclicks.some((o) => o.includes(`openBindSUByName('${n}')`))),
      };
    });
    expect(r.exists).toBe(true);
    expect(r.isSection).toBe(true);
    expect(r.count).toBe(7);
    expect(r.allRouted).toBe(true);
  });

  test('clicking a council member from the roster section opens their bind card (v120)', async ({ page }) => {
    await page.evaluate(() => {
      const sec = document.getElementById('binds-council')!;
      const link = Array.from(sec.querySelectorAll('.su-link'))
        .find((l) => (l.getAttribute('onclick') || '').includes("openBindSUByName('Bremm Sparkfist')")) as HTMLElement;
      link.click();
    });
    await page.waitForTimeout(120);
    const t = await page.evaluate(() => (document.getElementById('bindsu-detail')!.textContent || ''));
    expect(t).toContain('Bremm Sparkfist');
    expect(t).toContain('lightning priest');
  });

  test('binds stays demon-only: the roster note correctly flags the 8 regular minions as Human / NOT bindable (v121)', async ({ page }) => {
    // the v120 note wrongly said the 8 regular Council minions were "Demon-coded and bindable";
    // they are Human (per the demon-check bestiary) so Bind Demon cannot bind them. No non-demon
    // gets card treatment in the binds tab — only the corrected trap clarification remains.
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-council') as HTMLElement;
      const txt = sec.textContent || '';
      return {
        suLinks: sec.querySelectorAll('.su-link').length, // only the 7 named demon binds
        noMinionCard: !document.getElementById('council-minion-detail'),
        cannotBind: /cannot\s+bind/i.test(txt),
        human: txt.includes('Human'),
        notOldClaim: !/minions are\s+also\s+Demon-coded and bindable/i.test(txt),
      };
    });
    expect(r.suLinks).toBe(7);
    expect(r.noMinionCard).toBe(true);
    expect(r.cannotBind).toBe(true);
    expect(r.human).toBe(true);
    expect(r.notOldClaim).toBe(true);
  });

  test('no console errors opening every bind ID card', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    const names = await page.evaluate(() => ((window as any).BIND_SU || []).map((b: any) => b.name));
    for (const n of names) {
      await page.evaluate((nm) => (window as any).openBindSUByName(nm), n);
      await page.waitForTimeout(20);
    }
    expect(errs).toEqual([]);
  });
});
