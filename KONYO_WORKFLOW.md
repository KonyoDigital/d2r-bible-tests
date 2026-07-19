---
name: konyo-workflow
description: "THE KONYO WORKFLOW — his named, approved delivery pattern; run big arcs this way by default"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bbc4dc0a-c319-442f-95f9-3c845a12002e
---

Konyo named and blessed the delivery pattern (2026-07-17, the TV DIABLO v752–v766 arc):
**"ausome good workflow. Konyo Workflow it should be named."**

**The Konyo Workflow:**
1. **Konyo orders in bursts** — often mid-turn, with screenshots; fold every new order into the
   running plan without stopping the chain. Track phases as tasks; give him the checklist when asked.
2. **Army of specialist agents in parallel, zero file overlap** — Fable visual-coding-architect
   builds surfaces, Fable code-reviewer audits every substantive diff, general-purpose agents for
   extraction/housekeeping. ONE owner per file at a time; stand agents down explicitly on scope
   changes; snapshot dirty files before takeovers; re-grep before every edit (parallel-edit drift).
3. **Fable gates every merge** — suites (agent py / board Playwright / control py) + syntax gates +
   headless screenshots that are actually LOOKED at + real-tab MCP user passes. Version stamped,
   ledger entry (tv/PINGPONG_LOG.md rounds + BUILD_LOG + TRACKING + BUGS REG-NNN), commit, push,
   deploy. A version is not shipped until all gates pass.
4. **Grok = third eye** — post-ship pingpong rounds (Grok CLI when the MCP key is dead): critique →
   implement top picks → verify → GROK INSIGHTS in the ledger. Konyo may also route Grok to code
   waves directly ("Grok codes, Fable gates") — then verify Grok's ships against a pre-review
   trap checklist and fix what slipped (the v760.1 farewell class).
5. **Each round ships as its own version** (v748-750, v767-768… pattern); autonomous chains end
   with ONE final ping to Konyo summarizing the arc — he explicitly wants "ship them all
   autonomously and ping me when finished."

**MANDATORY SHIP PROTOCOL (Konyo, 2026-07-19 — 'yes its mandatory'):** EVERY shipped version,
by protocol, gets the full cycle — no exceptions, no skipping under momentum:
1. TDD: locks written for the change, full suites green (agent py + control py + Playwright).
2. UX/UI polish pass on any touched surface.
3. USER-EXPERIENCE TESTS: drive the real UI (headless playwright on the live app — the RINSE
   pattern: every button both directions, keyboard matrix, latency numbers) + screenshots that
   are actually looked at.
4. SuperGrok pingpong: post-ship back-pass on the diff (verify each claim, hunt one new bug,
   name upgrades) → its findings ship immediately as the next version.
…AND the whole usual ceremony (Konyo: 'not only those 4 — the whole thing we usually do'):
5. Patch discipline: anchors re-grepped against the LIVE file, count==1 asserts, single write at
   END, abort-without-write on drift (partial-applies burned us ×5).
6. Syntax gates every touched file: py ast.parse · UI new Function() parse · bash -n.
7. VISUAL verification: headless screenshots of every changed surface, actually LOOKED at
   (cinema-black and engine-console clutter were caught by eyes, not tests).
8. Version stamps EVERYWHERE, triple parity test-locked (agent VERSION == control ver == bible
   D2R_BUILD; footer Triple Lamp goes amber on drift).
9. Ledger: PINGPONG_LOG round entry per ship · BUGS.md REG-NNN for post-ship breakages ·
   memory updates for durable lessons.
10. Commit (Co-Authored-By Fable) → push through the smoke gate → Cloudflare deploy → app cycle
    ONLY when /api/status mode=off (REG-026: a background cycle killed a live run) → live probe
    of the shipped feature (curl the endpoint / drive the button) as acceptance.
11. Army of agents when scale demands (one owner per surface, patches delivered for MY gate);
    live-session sanctity: never restart anything while Konyo is ON AIR.
12. SELF-ENFORCING SUITE LAYER (Konyo 'add them too', 2026-07-19): the RINSE is a PERMANENT
    spec (tests/rinse.spec.ts), not an ad-hoc script · latency budgets are ASSERTED (status
    <100ms, button ack <200ms — regressions fail, never 'feel slow') · visual regression
    snapshots (Playwright toHaveScreenshot) on theatre/drawer/console · parse fuzz corpus on
    _parse_read · 30-min soak test asserting flat memory/fps (Grok endurance acceptance) ·
    CI stub-control harness so live-app e2e runs in CI too · pre-push hook auto-runs the tv
    fast lane (the gate becomes physically unskippable).
This protocol caught real catastrophes when followed (R16 dispatch-lie, R17 browser pin-race,
UX-driver's invisible-✕) — treat skipping ANY step as a doctrine break.

**Why:** he confirmed this shape repeatedly and named it; it survived a 25-version night.
**How to apply:** default to this for any multi-version arc on his projects; see
[[feedback-grok-pingpong-loop]] for the older nightly loop this generalizes.

## Step 13 — THE SEVEN-ROUND RULE (Konyo, 2026-07-19)
Every version upgrade LEVELS UP through the pingpong: **at least 7 back-and-forth rounds**
(Fable ↔ SuperGrok — design pass, implement, back-pass, fix, re-verify, polish pass, seal)
before a full cycle counts as complete. A version that got fewer than 7 exchanges is not
sealed — it is a draft. The rounds are logged per version in PINGPONG_LOG.md.
