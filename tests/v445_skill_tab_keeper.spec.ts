import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v445 — the magic/rare keeper must recognise skill-TAB bonuses whose name has no "Skill" word
// (Shadow Disciplines, Traps, Martial Arts, Warcries, Masteries, Auras, Curses) + class-restricted
// "+N to X (Class Only)" — Konyo's "+3 to Shadow Disciplines" amulet was being thrown out.
test('skill-tab amulets/charms are kept (incl. tabs without the word "Skill")', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1200);
  const r = await page.evaluate(() => {
    const w:any = window;
    const k = (mods:string[], base:string) => { const j = w._jewelryKeep(mods, base); return j && j.keep; };
    return {
      shadowDisc: k(['+3 to Shadow Disciplines (Assassin Only)', '+93 to Life'], 'Amulet'),  // Konyo's case
      fireSkills: k(['+2 to Fire Skills (Sorceress Only)'], 'Amulet'),
      trapsGC:    k(['+1 to Traps (Assassin Only)'], 'Grand Charm'),
      warcriesGC: k(['+1 to Warcries (Barbarian Only)'], 'Grand Charm'),
      allSkills:  k(['+1 to All Skills'], 'Amulet'),
      // negatives — a junk magic amulet with no real roll is NOT kept
      junkAmu:    k(['+5 to Energy', '+3 to Mana'], 'Amulet'),
      plus1tabAmu:k(['+1 to Shadow Disciplines (Assassin Only)'], 'Amulet'), // +1 tab alone is mediocre on an amulet
    };
  });
  expect(r.shadowDisc).toBe(true);
  expect(r.fireSkills).toBe(true);
  expect(r.trapsGC).toBe(true);
  expect(r.warcriesGC).toBe(true);
  expect(r.allSkills).toBe(true);
  expect(r.junkAmu).toBeFalsy();
});
