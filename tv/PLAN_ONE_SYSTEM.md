# 🔗 PLAN: ONE SYSTEM — auto-bridged engines + flagship TALLIES drilldown
_Konyo's order, 2026-07-20 live session: "i want this a one system working app... why is it not bridged automatically?" + "for the TALLIES engine i want to be able to see what exactly was tallied... RUNES for runes and GEMS for gems... flagship style... and chronicle too, everything synced properly and showing visually... it needs to connect to the console/website."_

## Ground truth from today's live debugging (all verified, do not re-derive)
- Agent → bridge → reads: **healthy**. `scene:stash, stashTab:runes` flows into `/state` correctly.
- The **auto-intake trigger lives ONLY in bible.html** (`tvStashAutoIntake` etc. ~L33667+). control_ui.html has ZERO intake code. If no bible board page is open and polling, **no tally/vault/chronicle engine runs at all**. This is the root "why is it not bridged automatically".
- The locked tally pipeline itself **works end-to-end**: manually invoking `tvStashAutoIntake('runes')` on a board counted the full rune stash from the live frame (31 rune types, El 14 … Cham 2) in ~60s.
- v927.5 fixed: bridge CORS preflight (intake_result POSTs from any board now journal → `TALLIES · synced` finally counts) and D2R process-alive fallback (loading screens no longer HOLD for minutes).
- ⚠️ **STORE SPLIT**: tallies land in the *invoking page's* localStorage. Chrome board, pywebview app board, and bull-4-u.com are THREE separate stores. Today's rune tally lives in Chrome's copy. "Connect to console/website" requires answering how the living treasury syncs across surfaces (bridge as source of truth? export/import? intake inbox the board drains on load?).

## Workstreams
1. **AUTO-BRIDGE (the "one system" core).** ON AIR must guarantee a live engine with zero clicks. Options, in preference order:
   a. Control app auto-navigates its webview to the SESSIONS board when the agent goes on air (one-window doctrine preserved; board auto-probes the bridge already).
   b. Move the intake *trigger* server-side: agent detects tally-tab deep read → POSTs frame into the locked intake path itself → results into a bridge-side inbox that any board drains into its store on load/poll. (Solves the store split too — bridge becomes truth.)
   Decide (a) fast-fix now + (b) as the real architecture; (b) must NOT rebuild the locked pipeline (v905 lock: Sonnet + crop config untouched — feed it Files/frames only).
2. **TALLIES flagship drilldown.** The TALLIES chip opens into three buttons — 🪨 RUNES · 💎 GEMS · 🧪 MATERIALS — each expanding a polished, aligned panel (flagship style like Forge v552): what was tallied, per-key counts with rune/gem art, delta vs previous shot, timestamp + the actual frame photo it came from (hist/<frameId>.jpg), and which engine lane fired it (auto-shot vs manual Tools 📸). Same in-game rarity colour discipline as everywhere.
3. **CHRONICLE visual sync.** Every intake/vault/read beat should land in the Chronicle surfaces visually (chips/cards), cross-referenced to frames — "everything synced properly and showing visually". Audit which beats currently reach the Chronicle vs die in per-surface stores.
4. **WATCHING = eye badge, not a curtain.** control_ui home: kill the full-screen WATCHING/HOLD/OFF splash while a session is live; keep the recent-frames slideshow (last good frames) with a small pulsing 👁 badge + one-line status. Splash only when there are genuinely no frames (fresh boot / true dormant).

## Grok third-eye round 1 (2026-07-20 eve) — deferred items for the arc
- **P0 (deferred, bounded):** engine window + a user-opened board can BOTH fire auto-intake (per-document `_stashVisitDone`/`_stashShutter`). SET semantics keep counts convergent, but it double-spends AI calls and double-journals shots. Fix = cross-document intake LEASE (bridge `/intake_claim` or shared-LS lock) — bible.html edit, EDIT_LOCK protocol.
- Funnel (±1 live vault) tallies live only in board LS (`d2r_tvdTallyLog`) — not in the journal, so not in the TALLY ENGINE drilldown. Treasury unification should journal funnel events through the bridge too.
- Engine liveness is lamp-only (`d2r_tvdOn` stamp). Real heartbeat: engine posts a beat to control every 30s; control alarms when silent + auto-respawns the window.
- WebKit persistent store now grows forever; needs a retention story. Also `#tvd-engine` hash is normalized away by the board — harmless today, but an explicit engine mode flag would let the board mute its own UI work off-screen.
- film-held cold-start: with no frame yet this session the stage still falls to the big word (correct today; revisit if Konyo wants last-SESSION's frame).

## v931 state + Konyo's console-UX order (2026-07-20 evening)
- ✅ Engine is now an invisible same-origin **iframe inside control_ui** (`#tvd-eng`, `/board?engine=1`) — one window, no side tile, driver via contentWindow. v928 second-window and v930 mini-tile approaches are dead.
- 🎯 NEXT UX ARC — **THE SHELL** (Konyo, twice, explicit list: "Tools / gems / stash / Sessions / FORGE / F·SETS / F·UNIQUES — a shell for it all, perfected"): unify console-home ↔ every board surface into ONE seamless shell — instant toggle-free switching (no page reloads) between Home · Sessions · Forge · F·Uniques · F·Sets · Tools · TV·D, shared state everywhere, the TALLY ENGINE / stash cards / vault ≤1 click from anywhere, and the console overlay (ON AIR / END SESSION / lamps) persistent on every surface. Flagship polish. Marquee of the next night arc.

## 🎯 THE TEXT-TRIGGERED EYE — the arc's centerpiece (forensic case 2026-07-20 18:37 session)
Konyo showed ~20 items; 4 reads landed, all of them the PERMANENT panel names (+1 lucky Death Torc). Frames prove the Materials tab sat open for 2 minutes with ZERO deep reads → no tab:materials read → driver had nothing to fire → materials never tallied. **Root architecture flaw: read triggering is pixel-motion/settle based — blind to tooltips appearing and sub-panel tab swaps.** ~20 tooltips lived and died between settle ticks.
**The fix (Konyo: "we need an AI automating every screenshot read — my backend to the ON AIR product"):**
- OCR EVERY film frame (the fast lane reads in 50-150ms — it can keep up with 1-5fps easily).
- Trigger deep reads on NEW TEXT, not pixel motion: a tooltip name OCR hasn't seen this visit → immediate priority read of THAT frame (the frame is already on disk — read the archived frame, not the live eye, so fast hovers can't escape).
- Stash-tab labels via OCR → tab-change detection even when the pixel delta is small → tally intakes fire on every tab visit reliably.
- The SECOND EYE (below) then sweeps the reel for anything the live lane still missed.
This turns the eye from "watches for stillness" into "reads everything that ever appears" — the ON AIR backend Konyo is asking for. 10x the visual debugger: every frame gets an OCR verdict journaled, so SIM can show text-seen-per-frame.

## 👁👁 THE SECOND EYE — trailing verify reader (Konyo's order, 2026-07-20 late)
_"a second engine AI reader that goes back and slowly thoroughly checks the first picture and slowly creeps up to the first main AI READER — fixing, checking, recalibrating… a second eye, different colored, so in simulation I can retro-check and debug surgically."_
- **Architecture:** a low-priority VERIFY reader with its own cursor that trails the live reader through the session's frames (hist/reel), re-reading each read-frame deeply (no time pressure: full-res, longer prompts, cross-check vs OCR + the live read's names). It creeps forward whenever the main pool is idle (never steals a live slot — the debt law applies) and catches up to LIVE − 1.
- **Output lane:** journal lane `verify` — each record links the ORIGINAL read (frameId + readId), verdict per name: confirmed / corrected(from→to) / missed(name the live eye didn't see) / phantom(live saw it, frame doesn't support it). Corrections cascade: tally/vault deltas re-applied through the same public adjust lanes with provenance.
- **SIM rendering:** two eyes, visually distinct — 🔴 main eye beats vs 🔵 second eye beats (different color chips/glow); scrubbing a frame shows both opinions side-by-side; disagreements flagged as ⚡ recal markers on the timeline so bugs can be pinpointed surgically. This IS the SIMULATION NORTH STAR's next chapter (tv/SIMULATION_SPEC.md).
- **Seed that exists already:** `TV_VERIFY` / `VERIFY_ON` + `_VERIFY_Q` in tv_diablo.py (fires re-reads when readers are free, ~L3312/3682/4310) — audit it first; the second eye should grow FROM this lane, not beside it.
- **Also needed (same arc):** intake early-exits journal a receipt (ok:false + why) so 'busy'/'no-frame' skips are visible in the drilldown; second-eye pass over tally shots (recount vs the shot photo).

## 🧠 KAI — THE CLOSER (layer 3, Konyo's order 2026-07-20 night)
_"a REAL MAIN HIDDEN KAI that's AI READING everything in backend terms after the closure of it all — peacefully, thoroughly, coded for perfection — to sync and automate everything that has been manual."_
The three-layer eye, complete:
- **L1 · 🔴 LIVE EYE** — real-time, fast, settle/text-triggered (see Text-Triggered Eye). Optimized for immediacy; allowed to miss.
- **L2 · 🔵 SECOND EYE** — trails the live eye during the session, re-verifying reads when the pool is idle.
- **L3 · 🧠 KAI THE CLOSER** — fires on session SEAL, hidden, zero time pressure. Walks the ENTIRE reel frame by frame (all footage + read frames) and produces the session's authoritative truth:
  1. **Full-reel re-read:** every frame with item-ish text gets a deep read at leisure (full-res, no debt law, batched through the subscription lane). Catches everything L1/L2 missed — the "20 items shown, 4 read" class dies here.
  2. **Auto-register on sight:** anything it reads that isn't in the Chronicle/grail/tally yet gets registered with provenance (frameId + timestamp) — "it read it, it analyzed it → it's registered. why not." Chronicle-firsts flagged 🆕 for the wall.
  3. **The mule/throw-out funnel:** items that got muled or thrown during the session are re-funneled through the AI ITEM CHECKER (the v455 keep-or-toss flagship) with the actual frame as evidence → corrected verdict journaled ("thrown ✓ correct" / "⚠ that was a keeper — it went out at 18:42, frame f_…"). Regret report per session.
  4. **Reconciliation ledger:** KAI's final pass diffs L1+L2 truth vs its own → one sealed session report (found / corrected / missed / phantom / registered / regrets) that the SHELF card and SIM surface as the session's closing chapter. All KAI beats journal on the same timeline, third color (🧠 gold?) — SIM shows all three minds per frame.
- **Architecture:** a control-side batch worker (like the engine driver) that wakes on seal, walks reel index.json, runs reads through the existing locked lanes (claude -p subscription; intake for tallies), throttled to idle (nice, one at a time) so it never fights the next live session. Resumable (cursor in the reel), survives app restarts.

## Guardrails
- 🔒 INTAKE LOCKED (d2r_intake_LOCKED.md): the vision/crop pipeline is untouchable — only supply frames to it.
- bible.html EDIT_LOCK protocol before any board edit.
- Playwright: smoke + targeted on Mac; full suite = CI/Windows.
- Ship per Konyo Workflow: version-per-round, Routine I verdict before sealing claims.

## 🧬 THE INTELLIGENCE STACK (Konyo's doctrine, 2026-07-20 close: "layers and layers of intelligence and brains working with analyzed and processed Diablo II specs — genius AI reader thoughts")
Every layer gets a D2R DOMAIN BRAIN, not just vision:
1. **Spec-grounded reading** — the reader's prompts and post-processing cross-reference the repo's own truth: 396 uniques / 136 sets / 523 bases / RotW runewords / rune+gem vocab. A read that returns "Harlequin Crost" snaps to Harlequin Crest because the DB says so; a name outside every DB flags itself as suspect instead of registering garbage.
2. **Layout templates** — hardcoded D2R screen geometry: equipment panel slots, inventory grid, stash grid + tab strip, ground-label zones, tooltip anatomy (name line color = rarity). Location tags (equipped/inventory/stash/ground) verified by GEOMETRY, not just the model's opinion. Rarity from pixel color cross-checked against the DB's rarity for that name.
3. **Expectation engine (the Watchdog)** — D2R-spec assertions per session: 3 tally tabs visited ⇒ 3 receipts; stash opened ⇒ tab reads exist; hover streak ⇒ text-eye triggers; charm/jewel shown ⇒ a read with a charm/jewel-shaped name. Misses become loud red beats, not silence.
4. **Genius thoughts, journaled** — each read's record grows a `reasoning` field: what the reader inferred (item class, rarity, why this location tag, which DB entry matched, confidence per claim) — the SIM shows the AI's actual thinking per frame, not just its answer.
5. **Cross-layer argumentation** — Eye 1 asserts, Eye 2 disputes with evidence, KAI arbitrates against the frame + DB. Disagreements journal as structured debates the SIM renders (⚡ beats expand into "eye 1 said X because…, eye 2 said Y because…, KAI ruled Z").

## 📸 KAI v2 = THE FUNNEL (Konyo's architecture call, 2026-07-20 night — this supersedes any idea of a new KAI reader)
_"We already have a perfected system that reads items perfectly with a full database — vault intake. The ON AIR photos should be funneled through THAT specific wiring… all our safeguards and layers of accuracy are already there, it spits it out the other side clean and routes it to where it's relevant. The whole session gallery run through that system as the 4th layer of accuracy — that's the real hidden automated KAI."_
- **LAW: KAI never gets his own reader.** He is a chauffeur for frames. The LOCKED intake system (vault 📸 / tally intakes / AI Item Checker — crops, majority vote, DB routing, rarity colors, keep-or-toss) is the one and only deep-analysis organ.
- **Mechanism (all pieces exist tonight):** post-seal, KAI classifies each reel frame cheaply (OCR text + layout template: stash-open / inventory-open / tooltip / gameplay) → fetches the frame same-origin from /hist → hands it to the matching LOCKED lane inside the engine iframe via the driver (window.vaultIntake([file]) / tally intakes / item-checker), throttled one-at-a-time, TV_KAI_MODEL knob (sonnet default, opus opt-in).
- **Output routing = the funnel's own:** vault/chronicle/tally entries with frameId provenance; mule/throw-out re-verdicts through the Item Checker; dedup by the existing SET/debt laws + receipt dedupe. Anything read that the chronicle lacks → registered, stamped with the frame that proves it.
- Layer picture: 🔴 live eye → 🔵 trailing verify → 🧠 KAI sweep (what was missed) → 📸 THE FUNNEL (the missed frames fed through the perfected pipeline). Layer 4 IS the hidden automated KAI.

## Grok shell-verdict backlog (2026-07-20 seal): #2 shell z-index/Esc discipline (board overlays inside the promoted iframe vs ⌂ pill at 960; Esc guard is dead code), #3 receipt dedupe ignores counts + empty-frameId bucket collapse, #4 badge honesty (🔵 should key off verify-lane activity, 🧠 off closer runs not just the driver probe; watchdog None-until-first-seal reads as clean).

## 🔬 v939 DESIGNED ROUND — tooltip frames → AI Item Checker (the regret funnel's engine)
Discovery done (2026-07-20 late): the Checker lives in bible.html ~28440-28470 — `window.aicUpload(file)` reads a photo into a SINGLE interactive draft (`_aicItem`), verdicts render to the card, `aicMule()/aicToss()` are human buttons. KAI cannot batch through this without clobbering the draft.
**Build:** a headless sibling `window.aicJudge(file) → Promise({name, base, q, mods, verdict, why})` that reuses the Checker's EXACT read prompt + verdict logic but touches no draft/UI. Then KAI: missed frames cls 'tooltip' → aicJudge → journal lane:'kai' rows with the verdict (keep/toss + why) → the REGRET REPORT: cross-reference against thrown/muled lifecycle tags ("you tossed X at 18:42 — the judge says keeper, frame attached"). EDIT_LOCK protocol; verdict rows feed a shelf-card 💔 regrets count and a SIM 🔬 beat.

## 🎛 BUTTONS+DEPTH ARC (Konyo 2026-07-20 ~23:50, live session evidence)
1. **Un-escapable panels (10 polish rounds ordered):** the intake/verdict side panel + drawer buttons trap the user after click — every overlay needs: Esc closes (layered), ✕ visible, click-outside closes, focus returns. Full button audit: hover/active/disabled states, hit areas ≥36px, no dead buttons.
2. **DEBUGGER DEPTH (his #1):** the at-this-instant card must go deeper — full dossier + the read's raw model text, OCR literal lines, decision chain per item, dispatch reasoning (interest parts), prompt ver — the /api/beat blob rendered BEAUTIFULLY, not just summary lines.
3. **FOOTAGE STARVE live @0.2fps** (banner during his 23:47 session; 55 film in 3m): film lane starving under game+reads load — diagnose grab timings (white-guard demotes? CPU nice? read.jpg conversions blocking?).
4. **Honesty note miscount:** said '0 stills' on a 55-film session — condition reads wrong field or fires pre-load.
5. **REAL pacing round 2 (Konyo: "REAL too fast" — live):** his header showed 'ran 3m01s · play ~1m @1×' with the pill on HIGHLIGHTS — (a) SIM/debugger entry must DEFAULT to REAL every open (never inherit highlights), (b) header play-estimate must recompute per mode and read '3m01s at true speed' in REAL, (c) verify REAL Tplay == session span on the starved 55-frame session specifically.

## 🚦 THE KAI ROUTER (Konyo's architecture call #2, 2026-07-20 ~23:55) — v944 arc
_"Before it gets funneled, after the film: every screenshot gets checked by all 4 brains, tagged/labeled, verified, and THEN routed to its appropriate funnel — items to VAULT MANAGER (mule/throw), GEMS to gems, RUNES to runes, MATERIALS to materials — each frame labeled, verified 1000%, then engine-wired to the perfected intake that already works for each."_
- **Stage 1 — THE LABEL TABLE (evidence, no firing):** post-seal, KAI emits a per-frame ROUTING LEDGER into kai_report.json: for EVERY frame — {frame, ts, label (stash-runes/gems/materials/vault-item/tooltip/gameplay), sources (which brains agree: ocr-words / journal-truth / read-name / judge), confidence (quorum count), route (which funnel WOULD take it), routed (what actually fired), skipReason}. The replayer/filmstrip can then badge every thumb with its label.
- **Stage 2 — QUORUM GATE:** a frame routes only at confidence ≥2 sources (label agreement); singles get flagged 🟡 for the drilldown instead of fired.
- **Stage 3 — ROUTE EXECUTION unification:** the existing funnel/judge/vault fires become CONSUMERS of the ledger (one router decides, lanes obey), each posting its receipt back onto the ledger row — full circle auditability: label → verify → route → receipt, per screenshot.
- Existing organs already provide: labels (journal-truth classes), lanes (tally/vault/judge via engine iframe), receipts (/intake_result, /kai_verdict). The router formalizes the middle and makes it visible.
- **DEDUPE LAW (Konyo addendum):** duplicate photos dedupe automatically INSIDE the router — near-identical consecutive frames (same sampled signature) chain to their first occurrence: label 'dup', route null, skipReason 'dup-of:<frame>'; only the FIRST of a visual run routes. Lanes can never double-fire on the same sight; the ledger shows the chain.
