import { test, expect } from './_net_stub';
import * as path from 'path';
import * as fs from 'fs';

// v538 — the AI intake must NEVER auto-mark a runeword as FORGED in the Chronicle from an OCR read. A read
// runeword NAME is ambiguous (UI text, a base's "can-make" list, a Forge-tab screenshot), so auto-ticking
// rwMade produced false "created" entries — Konyo fed the Forge screenshot to intake and Breath of the Dying /
// Eternity / Silence / Honor / Insight were all marked forged though never made. The intake still recognizes +
// mules a read runeword ("don't throw out an Enigma"); only the Chronicle auto-tick was removed. These guards
// assert the two auto-stamp code paths do not come back.

const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');

test('the intake runeword-rescue paths no longer auto-stamp rwMade (no-time date-stamp gone)', () => {
  // the two removed patterns — a rwMade[<rwvar>] = "<Mon> <D>, <Y>" stamp with NO time, inside the intake
  // runeword recognition. (The MANUAL rwToggleMade stamp is different: it appends " · HH:MM".)
  expect(SRC).not.toContain("rwMade[rw]=_mo+' '+_d.getDate()+', '+_d.getFullYear()");
  expect(SRC).not.toContain("rwMade[_rwk]=_mo+' '+_dd.getDate()+', '+_dd.getFullYear()");
});

test('both intake runeword blocks carry the v538 "do not auto-mark forged" note', () => {
  // both recognition paths (render-time throw-out rescue + intake-time recognition) document the Chronicle stays manual
  const notes = (SRC.match(/DO NOT auto-mark/gi) || []).length;
  expect(notes).toBeGreaterThanOrEqual(2);
});

test('the MANUAL Chronicle toggle still stamps with a time (unchanged)', () => {
  // rwToggleMade must still record a full timestamp so "Undo last" / Completed ordering works
  expect(SRC).toContain("· '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')");
});
