import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v572 — NON-GAME SCREENSHOT REJECTION (live incident 2026-07-04 22:23): Konyo screenshotted his own
// tracker WEBSITE; the intake read item names off the web page's review cards and re-registered them as
// fresh loot — phantom ×2 copies (Devil Star, Small Crescent) and a review card whose "photo" was the
// bible page itself (Blade Bow). The intake prompts now open with a gate: decide whether the image is the
// DIABLO II GAME CLIENT at all — browser/desktop chrome or the "D2R Farming Bible" dashboard → return
// empty for every field. Locked here as prompt-content assertions (the prompt is the behavior contract).

const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'functions', 'api', 'intake.js'), 'utf8');

test('the items prompt gates on game-client-or-nothing and names the bible dashboard as a rejection', () => {
  expect(SRC).toContain('is this the DIABLO II GAME CLIENT at all');
  expect(SRC).toContain('D2R Farming Bible');                       // the user's own tracker is called out
  expect(SRC).toMatch(/non-game screenshot return EMPTY arrays/i);  // hard empty, not best-effort reads
  // the old loophole that let web pages count as a readable source is gone from the items prompt
  expect(SRC).not.toContain('OR a store/web listing line');
});

test('the raw-name rescue prompt carries the same non-game gate', () => {
  const raw = SRC.slice(SRC.indexOf('const rawText'));
  expect(raw).toContain('NOT the Diablo II game client at all');
  expect(raw).toContain('return name=""');
});
