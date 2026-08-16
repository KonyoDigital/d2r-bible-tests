import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1728 — A FEATURE THAT DISABLES ITSELF MUST SAY WHY.
//
// The photo intake detects the Anthropic key's monthly usage limit in seven places. ONE of them
// set both the flag and the banner text; the six retry/fallback paths set only the flag, so
// hitting the cap on a fallback silently suppressed the read with nothing on screen.
//
// That matters more than a normal missing error, because the message exists precisely to say
// "This is NOT your screenshots — they are fine." Without it, a capped key is indistinguishable
// from the AI failing to read his photos, and he would go re-shooting screenshots that were fine.
//
// The named wrapper that did both (_aiReadJson) had ZERO callers — every site hand-rolled the
// guard, which is how they diverged. It is now _aiLimitSeen, and every site calls it.
//
// This gate pins the invariant: raising the flag and explaining it are ONE act.

const BIBLE = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');

test.describe('v1728 — the AI limit explains itself', () => {
  test('★★★ nothing sets the limit flag except the shared helper', async () => {
    const raw = [...BIBLE.matchAll(/_aiLimitHit\s*=\s*true/g)].map((m) => {
      const line = BIBLE.slice(0, m.index || 0).split('\n').length;
      const src = BIBLE.split('\n')[line - 1];
      return { line, src: src.trim().slice(0, 90) };
    });
    // exactly one assignment may exist: the one inside _aiLimitSeen
    const outside = raw.filter((r) => !/function _aiLimitSeen/.test(r.src));
    expect(raw.length, 'assignments to _aiLimitHit').toBe(1);
    expect(outside, 'a site raises the limit flag without going through _aiLimitSeen: ' +
      outside.map((o) => `bible.html:${o.line}`).join(', ')).toEqual([]);
  });

  test('★★ every limit detection routes to the helper', async () => {
    // every `_aiIsLimit(x)` test must lead to _aiLimitSeen(x) on the same line
    const bad: string[] = [];
    for (const m of BIBLE.matchAll(/if \(_aiIsLimit\(([^)]*)\)\)([^\n]{0,120})/g)) {
      if (!/_aiLimitSeen\(/.test(m[2])) {
        const line = BIBLE.slice(0, m.index || 0).split('\n').length;
        bad.push(`bible.html:${line} — detects the limit but does not explain it`);
      }
    }
    expect(bad, bad.join(' | ')).toEqual([]);
  });

  test('★ the helper still carries the sentence that matters', async () => {
    expect(BIBLE, 'the "not your screenshots" reassurance is the point of the message')
      .toContain('This is NOT your screenshots');
  });
});
