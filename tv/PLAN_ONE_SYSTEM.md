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
- 🎯 NEXT UX ARC (Konyo: "inside the console all the tools and gems and stash and everything should be smooth and working and toggle-free and toggle-easy in between each other"): unify console-home ↔ board surfaces into one seamless shell — instant tab switching (no page reloads between home/Sessions/Tools/Forge), shared state, the TALLY ENGINE / stash cards / vault reachable in ≤1 click from anywhere, and the console overlay (ON AIR / END SESSION) persistent across every surface. Design flagship-style; this is the marquee of the next night arc alongside the TALLIES drilldown data-unification items above.

## Guardrails
- 🔒 INTAKE LOCKED (d2r_intake_LOCKED.md): the vision/crop pipeline is untouchable — only supply frames to it.
- bible.html EDIT_LOCK protocol before any board edit.
- Playwright: smoke + targeted on Mac; full suite = CI/Windows.
- Ship per Konyo Workflow: version-per-round, Routine I verdict before sealing claims.
