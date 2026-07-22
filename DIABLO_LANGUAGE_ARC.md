# 🗣️🎮 DIABLO-LANGUAGE AI READER ACCURACY — 10-round arc (Konyo 2026-07-22)

> Konyo: "i need [the AI reads] really accurately for each of what it's reading even in retro to pinpoint what's
> happening in-game.. the codes there i don't understand, i want them keyworded to in-game.. for a PORTAL or
> entering a game it says 'AI READER near black screen' — but it's just entering a game / going through a portal..
> for all the AI reads and analyzes i want it pinpoint-pointed with DIABLO LANGUAGE, coded, HARDCODED and SYNCED."
> "add this to tasks and give this a proper 10 rounds."

## THE KEY INSIGHT (grounded)
The engine ALREADY speaks Diablo. The read prompt (tv_diablo.py ~97-99) classifies every frame as
`scene = town | stash | inventory | loot | gameplay | transition`, where **transition = fullscreen loading/portal
art (burning fire portal, act loading screen, or a dark NO-HUD frame) = the player entering a portal/waypoint/area**,
plus `area` = zone name (ENTERING banner / automap / top-right Game block). There's even known-dead-frame learning
for the loading/portal screen (v741-742). BUT the reconciler (_kai_frame_cls @ control_app.py:2377, kaiClasses)
COLLAPSES this rich scene → generic gameplay/stash/tooltip before it reaches the labels + retro. So "entering a
portal" surfaces as "gameplay near black screen." THE ARC = carry the Diablo scene all the way through: preserve it
in classification, sync it to the UI live + retro, keyword it in hardcoded Diablo language, and sharpen detection of
the clear states so every read is pinpointed in-game.

## IRONCLAD
- TRUTHFUL — label only what the read actually supports; ambiguous frame = honest "unclear", never a wrong guess.
  Sealed reel wins in retro. Inherit eyes-pulse honesty.
- HARDCODED + SYNCED — ONE Diablo-language dictionary (states/events/areas) used EVERYWHERE (live console · Theatre
  retro · session fingerprint). No drift between live and retro (Konyo's "synced").
- LIGHT — no new heavy CV; ride the existing read/scene the AI already produces + cheap frame heuristics
  (black/dark/no-HUD detection is cheap). Don't lag the game.
- DON'T rework the read prompt's proven scene taxonomy or the known-dead-frame learning — SURFACE it, don't replace.
- Cadence: team-lead owns engine (tv_diablo.py/control_app.py reconciler+scene); polish-ui-2 owns control_ui.html
  labels; Fable gates each round; floor green; version-per-round.

## THE 10 ROUNDS
1. **CARRY THE SCENE THROUGH** — preserve the read's Diablo scene (town/stash/inventory/loot/gameplay/transition)
   + area in _kai_reconcile / _kai_frame_cls output + kaiClasses, instead of collapsing to gameplay/stash/tooltip.
   The Diablo scene must survive to the session + retro. [engine]
2. **PORTAL / LOADING = "entering game · portal"** (the reported bug) — a black/dark NO-HUD frame → "🔥 transition ·
   taking a portal / entering game / loading", NOT "near black screen". Hardcode the detection (tie to v741 learned
   loading frame + black-frame heuristic). [engine]
3. **AREA / ZONE in Diablo terms** — surface `area` (zone from ENTERING banner / automap) accurately per frame. [engine+UI]
4. **TOWN vs FARMING** — distinguish town (safe, no drops) from loot/gameplay (farming) in Diablo language. [engine+UI]
5. **SCENE KEYWORD CHIPS (live)** — show the current Diablo scene prominently in the console: 🔥 PORTAL · 🏛 TOWN ·
   🎒 STASH · ⚔ FARMING · 🔍 ITEM. Replaces opaque codes. [UI]
6. **RETRO SCENE SYNC** — the Theatre/session replay labels each frame's Diablo scene, so last-session review
   pinpoints what's happening in-game (Konyo: "even in retro"). [UI]
7. **SESSION SCENE FINGERPRINT** — the run's Diablo breakdown: "this run: 62% farming · 18% stash · 3 portals · 2
   town trips · 4 areas." [engine+UI]
8. **ITEM-READ DIABLO PRECISION** — uniques/sets/runes/gems labeled with exact Diablo rarity/name (extend the vocab
   grounding); a tooltip = "🔍 inspecting <item>". [engine]
9. **THE HARDCODED DICTIONARY** — one canonical Diablo-language map (states · events · acts/areas · rarities), the
   single source used live + retro + session. The "coded, hardcoded, synced" ask made literal. [engine+UI]
10. **ACCURACY PASS + edge states** — verify labels against real session frames (last session), handle ambiguity
    honestly, sync everywhere, polish. [engine+UI]

## FOOTAGE STARVE (Konyo "the starve thing is OK?")
0.3fps archive is OK/transient WHEN on a black loading/portal screen — nothing to capture, recovers when gameplay
resumes. Only a real problem if it PERSISTS during active gameplay (the v944 dark-frame-rejection issue, since
fixed). This arc actually FIXES the confusion: that black moment reads as "🔥 entering game / portal", not a starve.

## QUEUE (2026-07-22): 1) Console home fix (round 4, in flight → v1252) · 2) THIS + Sessions flagship interleave
after. Both are big arcs; run Diablo-Language rounds and Sessions rounds in sequence, gating each. 🗣️🎮🥷
