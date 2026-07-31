import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1517 — PLAIN D2R WORDS FIRST, system words muted underneath (Konyo's task #8), and the Chronicle
// speaking that same language (task #10).
//
// The rule is not "hide the system word" — he debugs with it, and hiding it would cost him the thing
// he uses when a read goes wrong. The rule is that HIS game's word leads and the engine's word
// trails, muted. A row that read "· stash @ Harrogath" put the engine first and his game nowhere.

const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

// the client dictionary is a plain object literal in the console — read it out rather than
// duplicating it, so this spec tracks the real thing
function dict(): Record<string, any> {
  const m = UI.match(/var _DIABLO_SCENES = \{([\s\S]*?)\n  \};/);
  expect(m, 'the scene dictionary must still be findable').toBeTruthy();
  const out: Record<string, any> = {};
  for (const line of (m![1] || '').split('\n')) {
    const e = line.match(/^\s*'?([a-z-]+)'?:\s*\{\s*ic:\s*'([^']*)',\s*key:\s*'([^']*)',\s*full:\s*'([^']*)'/);
    if (e) out[e[1]] = { ic: e[2], key: e[3], full: e[4] };
  }
  return out;
}

test.describe('v1517 — his game speaks first', () => {
  test('the CHRONICLE is in the dictionary every surface reads from', async () => {
    const d = dict();
    expect(Object.keys(d).length).toBeGreaterThan(6);
    expect(d['chronicle']).toBeTruthy();
    expect(d['chronicle'].key).toBe('CHRONICLE');
  });

  test('★ the two ledgers are named APART, and the unknown one claims neither', async () => {
    const d = dict();
    expect(d['chronicle-uniques'].full).toMatch(/grail/i);
    expect(d['chronicle-sets'].full).toMatch(/set/i);
    expect(d['chronicle-uniques'].ic).not.toBe(d['chronicle-sets'].ic);
    // the tab-less entry must not imply either ledger — it is what a reader shows when it wasn't sure
    expect(d['chronicle'].full).not.toMatch(/grail|set-piece/i);
  });

  test('the receipts row leads with the Diablo label, not the scene string', async () => {
    // the old shape put esc(b.scene) first with no game word at all
    const row = UI.slice(UI.indexOf('📖 IT SAW'), UI.indexOf('📖 IT SAW') + 2200);
    expect(row).toContain('_diabloScene(b.scene');
    expect(row).toContain('ar-dl');
    expect(row).toContain('ar-dl-sys');
    // and the system word survives — muted, not deleted
    expect(row).toMatch(/ar-dl-sys[^]*esc\(b\.scene\)/);
  });

  test('the forensics read-trail speaks it too', async () => {
    const trail = UI.slice(UI.indexOf('var trail = frames.map'), UI.indexOf('var trail = frames.map') + 900);
    expect(trail).toContain('_diabloScene(fr.scene');
    expect(trail).toContain('fx-dl-sys');
  });

  test('★ an unknown scene still shows SOMETHING — the fallback is never blank', async () => {
    // _diabloScene returns null for engine-internal scenes (kai/intake). Both surfaces must fall
    // back to the raw word rather than rendering an empty space where a label should be.
    const row = UI.slice(UI.indexOf('📖 IT SAW'), UI.indexOf('📖 IT SAW') + 2200);
    expect(row).toMatch(/if \(!d\) return[^]*esc\(b\.scene\)/);
    const trail = UI.slice(UI.indexOf('var trail = frames.map'), UI.indexOf('var trail = frames.map') + 900);
    expect(trail).toMatch(/:\s*' · '\+esc\(fr\.scene\)/);
  });

  test('the muted style is the SAME rule the theatre caption already uses', async () => {
    // one rule, applied everywhere — not three surfaces each inventing their own hierarchy
    for (const cls of ['th-dl-sys', 'ar-dl-sys', 'fx-dl-sys']) {
      const i = UI.indexOf('.' + cls + ' {');
      expect(i, cls + ' must be styled').toBeGreaterThan(0);
      const rule = UI.slice(i, i + 220);
      expect(rule, cls + ' must be muted').toMatch(/opacity:\s*\.[0-9]/);
      expect(rule, cls + ' must be the small mono trailing word').toContain('--fs-2xs');
    }
  });
});
