// v203 — THE VAULT mule manager (Tools centerpiece). Roster of mule "lockers"
// (default = the 10-mule warehouse blueprint), taxonomy auto-assign over the
// ✓ Owned pool (ITEM_CODEX base/rarity/setName + ITEM_TIP b/t fallback),
// drag-and-drop + click-assign, manifests export, and a 🏦 location badge on
// the item detail card. Persists d2r_muleRoster/d2r_muleAssign (rides backup).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const OWNED = ['Harlequin Crest (Shako)', 'The Stone of Jordan', 'Vampire Gaze',
  'Annihilus', 'Stormshield', 'Raven Frost', 'Tal Rasha set (any piece)', 'Windforce'];

test.describe('v203 the vault', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(2200);
    await page.evaluate((names) => {
      localStorage.removeItem('d2r_muleRoster');
      localStorage.removeItem('d2r_muleAssign');
      names.forEach((n: string) => eval('owned').add(n));
      (window as any).switchTab('tools');
      (window as any).renderVault();
    }, OWNED);
  });

  test('default roster renders 10 lockers (v360: + SHARED STASH; v342: + MAGIC & RARE); owned items appear as dock chips', async ({ page }) => {
    const r = await page.evaluate(() => ({
      mules: document.querySelectorAll('.vault-mule').length,
      chips: document.querySelectorAll('.vault-dock .vault-chip').length,
      names: [...document.querySelectorAll('.vm-name')].map(e => e.textContent),
    }));
    // v230: runes/essences/shards/statues → shared stash (RUNES-HIGH + MATS removed, 10→8).
    // v342: + MAGIC & RARE (8→9). v360: + SHARED STASH locker for the never-muled items (9→10).
    // v405: + RUNEWORDS locker (all forged runewords, weapon or armor) (10→11).
    expect(r.mules).toBe(11);
    expect(r.names).toContain('RUNEWORDS');
    expect(r.names).toContain('SHARED STASH');
    expect(r.names).toContain('MAGIC & RARE');
    expect(r.names).not.toContain('RUNES-HIGH');
    expect(r.names).not.toContain('MATS');
    // v227: 'Tal Rasha set (any piece)' is a grail ODDS row, not a physical
    // item — aggregates keep their calc ✓ but never become vault chips
    expect(r.chips).toBe(OWNED.length - 1);
    expect(r.names).toContain('SETS-TAL-IK');
    expect(r.names).toContain('UNI-SMALL');
  });

  // v226 — the AI-misread eraser: dock chips carry an ✕ that removes the
  // ✓ owned mark itself (not just the assignment), persisted. Born from the
  // 2026-06-13 incident: a pre-v225 scan registered Ist rune / Jah-Ber-Sur
  // rune / Tal Rasha set off a no-tooltip shards screenshot.
  test('v226 dock chip ✕ un-owns the item, persists, and leaves other items alone', async ({ page }) => {
    const r = await page.evaluate(() => {
      const chip = [...document.querySelectorAll('#vault-dock .vault-chip')]
        .find((c: any) => c.dataset.vaultItem === 'Windforce') as HTMLElement;
      const btn = chip?.querySelector('.vc-unown') as HTMLElement;
      btn?.click();
      return {
        hadBtn: !!btn,
        stillOwned: eval('owned').has('Windforce'),
        otherKept: eval('owned').has('Stormshield'),
        chipGone: ![...document.querySelectorAll('#vault-dock .vault-chip')]
          .some((c: any) => c.dataset.vaultItem === 'Windforce'),
        persisted: !JSON.parse(localStorage.getItem('d2r_owned') || '[]').includes('Windforce'),
      };
    });
    expect(r.hadBtn).toBe(true);
    expect(r.stillOwned).toBe(false);
    expect(r.otherKept).toBe(true);
    expect(r.chipGone).toBe(true);
    expect(r.persisted).toBe(true);
  });

  test('taxonomy: sets→set lockers, jewelry/charms→small, helms/shields→armor; shared-stash items never mule', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sug = (n: string) => { const s = (window as any).vaultSuggest(n); return s ? s.id : null; };
      return {
        tal: sug('Tal Rasha set (any piece)'), soj: sug('The Stone of Jordan'),
        gaze: sug('Vampire Gaze'), storm: sug('Stormshield'),
        anni: sug('Annihilus'), wf: sug('Windforce'),
        // v230 shared-stash guard: these must never get a mule (returns null)
        rune: sug('Ber Rune'), essence: sug('Essence of Hatred'),
        shard: sug('Worldstone Shard (Deep)'), statue: sug("Madawc's Ire"),
      };
    });
    expect(r.tal).toBe('sets-major');
    // v364: high trade-value items ("worth keeping close") auto-route to the SHARED cross-account stash
    // instead of their slot mule. SoJ is 'high' value → shared.
    expect(r.soj).toBe('shared');
    expect(r.gaze).toBe('uni-armor');   // med value → its slot mule
    expect(r.storm).toBe('uni-armor');  // low value → its slot mule
    // v409: Annihilus (like Hellfire Torch / Gheed's Fortune) only works in the ACTIVE character's
    // inventory — never muled and not shared (a charm in shared stash does nothing). → __keep sentinel.
    expect(r.anni).toBe('__keep');
    expect(r.wf).toBe('uni-weap');      // med value → its slot mule
    // shared-stash items are explicitly excluded from muling
    expect(r.rune).toBeNull();
    expect(r.essence).toBeNull();
    expect(r.shard).toBeNull();
    expect(r.statue).toBeNull();
  });

  // v227 — the vault holds EXACT set pieces, never fabricated aggregates
  // (Konyo: '"Tal Rasha any piece"?? needs the exact individual item within
  // the set, and size accordingly — can't be fabricated').
  test('v227 exact set pieces: in the dock with slot-true sizes + set-locker routing; aggregate stays out', async ({ page }) => {
    const r = await page.evaluate(() => {
      eval('owned').add("Tal Rasha's Guardianship");
      eval('owned').add("Trang-Oul's Girth");
      (window as any).renderVault();
      const chips = [...document.querySelectorAll('#vault-dock .vault-chip')].map((c: any) => c.dataset.vaultItem);
      return {
        pieceVocab: (window as any).__setPieceNames().length,
        aggInDock: chips.includes('Tal Rasha set (any piece)'),
        guardInDock: chips.includes("Tal Rasha's Guardianship"),
        girthInDock: chips.includes("Trang-Oul's Girth"),
        guardSize: eval('vaultSize')("Tal Rasha's Guardianship"),   // armor → 2×3
        girthSize: eval('vaultSize')("Trang-Oul's Girth"),          // belt → 2×2 row family
        crestSize: eval('vaultSize')("Tal Rasha's Horadric Crest"), // helm → 2×2
        adjSize: eval('vaultSize')("Tal Rasha's Adjudication"),     // amulet → 1×1
        guardSug: (window as any).vaultSuggest("Tal Rasha's Guardianship").id,
        girthSug: (window as any).vaultSuggest("Trang-Oul's Girth").id,
      };
    });
    expect(r.pieceVocab).toBeGreaterThanOrEqual(50);
    expect(r.aggInDock).toBe(false);
    expect(r.guardInDock).toBe(true);
    expect(r.girthInDock).toBe(true);
    expect(r.guardSize).toEqual([2, 3]);
    expect(r.crestSize).toEqual([2, 2]);
    expect(r.adjSize).toEqual([1, 1]);
    expect(r.guardSug).toBe('sets-major');
    expect(r.girthSug).toBe('sets-rest');
  });

  test('v227 AI intake registers the exact piece AND ✓s the set grail row (calc-only)', async ({ page }) => {
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ["Tal Rasha's Lidless Eye"], unrecognized: [], usage: { in: 700, out: 20, cached: 0 } }),
      })
    );
    await page.evaluate(() => localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake'));
    await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const f = new File([bytes], 'shot.jpg', { type: 'image/jpeg' });
      await (window as any).vaultIntake([f]);
    }, '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==');
    const r = await page.evaluate(() => ({
      piece: eval('owned').has("Tal Rasha's Lidless Eye"),
      grailRow: eval('owned').has('Tal Rasha set (any piece)'),
      chips: [...document.querySelectorAll('#vault-dock .vault-chip, .vm-item-row')].map((c: any) => c.dataset?.vaultItem || c.textContent),
      assigned: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}')["Tal Rasha's Lidless Eye"],
    }));
    expect(r.piece).toBe(true);
    expect(r.grailRow).toBe(true);             // grail ✓ rides along
    expect(r.assigned).toBe('sets-major');     // auto-filed to SETS-TAL-IK
  });

  test('auto-assign empties the dock, persists, and survives reload', async ({ page }) => {
    await page.evaluate(() => (window as any).vaultAutoAssign());
    const r1 = await page.evaluate(() => ({
      chips: document.querySelectorAll('.vault-dock .vault-chip').length,
      stored: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'),
    }));
    expect(r1.chips).toBe(0);
    // v364: SoJ is high trade value → auto-routes to the SHARED cross-account stash, not uni-small.
    expect(r1.stored['The Stone of Jordan']).toBe('shared');
    // persist owned BEFORE reloading — the vault prunes assignments of
    // un-owned items at load (eval('owned').add bypasses persistence)
    await page.evaluate(() => localStorage.setItem('d2r_owned', JSON.stringify([...eval('owned')])));
    await page.reload();
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(2200);
    const r2 = await page.evaluate(() => {
      (window as any).renderVault();
      const shared = document.querySelector('[data-vault-mule="shared"]')!;
      return { sharedCount: shared.querySelector('.vm-count')!.textContent, stored: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}')['The Stone of Jordan'] };
    });
    expect(r2.stored).toBe('shared');                  // assignment persisted across reload
    expect(Number(r2.sharedCount)).toBeGreaterThanOrEqual(1); // SoJ in the SHARED locker
  });

  test('click-assign (chip → locker) and unassign round-trip', async ({ page }) => {
    await page.evaluate(() => {
      const chip = [...document.querySelectorAll('.vault-chip')].find(c => (c as HTMLElement).dataset.vaultItem === 'Windforce') as HTMLElement;
      chip.click();
    });
    await page.evaluate(() => {
      (document.querySelector('[data-vault-mule="wip"] .vm-plate') as HTMLElement).click();
    });
    const r = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'));
    expect(r['Windforce']).toBe('wip');
    await page.evaluate(() => (window as any).vaultUnassign('Windforce'));
    const r2 = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'));
    expect(r2['Windforce']).toBeUndefined();
  });

  test('the 🏦 location badge renders on the item detail card and jumps to the vault', async ({ page }) => {
    await page.evaluate(() => {
      (window as any).vaultAssign('Harlequin Crest (Shako)', 'uni-armor');
      (window as any).openItemDetail('Harlequin Crest (Shako)');
    });
    const badge = await page.evaluate(() => document.querySelector('#item-detail-panel .vault-loc-badge')?.textContent || '');
    expect(badge).toContain('UNI-ARMOR');
    await page.evaluate(() => (document.querySelector('#item-detail-panel .vault-loc-badge') as HTMLElement).click());
    await page.waitForTimeout(500);
    const tab = await page.evaluate(() => (document.querySelector('.tabs .tab.active') as HTMLElement)?.dataset.tab);
    // v2084 gave the Vault Manager a main tab of its own and v2090 forwarded every old address to
    // it: window.vaultJump — the handler this badge fires (bible.html:35377) — now calls
    // switchTab('vault') (bible.html:35382), not switchTab('tools'). The law is unchanged, the
    // room moved: the badge must land him where the card actually is.
    expect(tab).toBe('vault');
  });

  test('manifests export copies markdown; add/rename/delete mule round-trip', async ({ page }) => {
    const r = await page.evaluate(async () => {
      (window as any).vaultAutoAssign();
      let copied = '';
      (navigator.clipboard as any).writeText = (t: string) => { copied = t; return Promise.resolve(); };
      (window as any).vaultExport();
      await new Promise(res => setTimeout(res, 100));
      (window as any).prompt = () => 'TEST-MULE';
      (window as any).vaultAddMule();
      const added = [...document.querySelectorAll('.vm-name')].some(e => e.textContent === 'TEST-MULE');
      (window as any).confirm = () => true;
      const id = JSON.parse(localStorage.getItem('d2r_muleRoster')!).find((m: any) => m.name === 'TEST-MULE').id;
      await (window as any).vaultDeleteMule(id);   // v341.60 — async (awaits uiConfirm); await before checking it's gone
      const gone = ![...document.querySelectorAll('.vm-name')].some(e => e.textContent === 'TEST-MULE');
      return { copied: copied.slice(0, 200), added, gone };
    });
    expect(r.copied).toContain('# The Vault — mule manifests');
    expect(r.copied).toContain('SETS-TAL-IK');
    expect(r.added).toBe(true);
    expect(r.gone).toBe(true);
  });

  test('no console errors through the full vault flow', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.evaluate(() => {
      (window as any).vaultAutoAssign();
      (window as any).renderVault();
      (window as any).openItemDetail('Stormshield');
    });
    await page.waitForTimeout(500);
    expect(errs).toEqual([]);
  });
});
