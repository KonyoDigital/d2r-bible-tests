# 📺 TV DIABLO — 🏓 PINGPONG NIGHT LOG (2026-07-15 → 16)

> The public round-by-round ledger of the TV-specific pingpong run (Konyo's order:
> "full TDD and test suites + ping-pong upgrades — ship at least 10 versions,
> end-to-end, verified in between"). **Ownership (2026-07-16):** Grok owns the
> **TV-KAI surface only** (`tv/**` agent + this ledger + TV README). Bible/forge/
> chronicles stay untouched. Constraint stack: read-only scanner · player's own
> Claude subscription · Sonnet for reads · no fabrication.

## State entering the night (v710.6b)
- Live run #1 verdict: capture ✓ · settle detector ✓ (fired exactly at pauses) ·
  bridge ✓ · board ✓ · **vision ✗ — every read hit the 180s timeout** (claude's
  Read choked on the 16MB raw BMP). Konyo saw "reads every ~3 minutes" = the
  timeout cadence, not the design.
- Fixed pre-night: BMP→1568px JPEG before vision (sips, ~300KB) · timeout 90s ·
  🧠 brain log (agent event ring → board panel: settles/skips-with-reasons/reads) ·
  stale sim flag cleared on boot · nested-Claude warning · README bare-terminal note.
- **Not yet re-tested live** — Konyo closed the agent; next launch picks it all up.

## Rounds

### R1 · v711 — TDD foundation: TV_STUB seam + agent test suite ✅
- `TV_STUB=1` makes `claude_read` return canned reads from `tv/stub_manifest.json`
  (basename key, `*` fallback) — the FULL agent loop runs with zero vision cost.
- `TV_PORT` env override (tests + port-conflict recovery).
- `tv/test_agent.py` (stdlib unittest, synthetic BMPs — no fixtures): 9/9 green —
  sig invariants (identical=0 · ±10 flicker settles · half-screen swing = motion ·
  None = 1.0) · loading-guard threshold · stub manifest · event-ring cap 60 ·
  live bridge GET /state + /ping with beat merge.

---

## GROK OWNERSHIP LOG (TV-only · ships code in `tv/**`)

### R11 · v720 / v720.1 — auth path + worker lock (live run #2 → #3) ✅ suite 19/19
- **Run #2 (v719.2, 2026-07-16 ~19:49 IDT):** agent fresh, transport OK (`read.jpg` 391KB),
  child had `--strict-mcp-config`, settle fired — but warm “didn't answer” and oneshot hit
  90s `cap` → honest-empty reads. Not a JPEG problem anymore.
- **Root cause:** shell `ANTHROPIC_API_KEY` makes headless `claude -p` prefer API auth over
  Claude subscription login. Probe: **with key → 40s timeout empty**; **key stripped →
  text `pong` in ~7s, image read JSON in ~21s**.
- **v720 fix:** `_claude_env()` strips `ANTHROPIC_API_KEY` + `ANTHROPIC_AUTH_TOKEN` for
  worker spawn and oneshot; one-time brain `vision auth: stripped …`. Parent shell unchanged.
- **Live proof after restart:** `vision warm — session ready in 14s` · oneshot **15.9s** ·
  warm reads **6.8s / 9.3s** (honest empty when not on D2R loot — correct).
- **v720.1:** worker `ask()` lock (warm thread vs settle-read race caused “non-JSON” on first
  fire) · persist `mode` on state reads · suite **19/19**.
- **Scope:** `tv/**` only. No bible / forge / chronicles.

### R12 · v723 — Haiku speed + genius Sonnet escalate + farmed→vault wire
- **Fast model:** `TV_MODEL=haiku` (warm worker). **Genius:** auto-escalate to
  `TV_MODEL_ESCALATE=sonnet` when conf low / empty loot / shaky farmed names.
  Cap `TV_ESCALATE_CAP=40`. Subscription only (API key still stripped).
- **Intent:** loot→`seen` (review-first) · inv/stash→`farmed` (auto engines + vault).
- **Vault:** new thin `window.tvVaultRegister(name)` — reuses owned + suggestMule +
  muleAssign from intake. **No photo AI. No vault redesign.** Floor never auto-files.

### R13 · v724 — SESSION HISTORY board (pre run #3)
- TV tab panel: LIVE / LAST SESSION · clock-time rows · HD art · HIT/DB/NO DB badges
  against engines + ~1400 ITEMS · farmed vault tags · last vision JPEG via `GET /frame`.
- Persisted `d2r_tvdHist` (account-forked) so last session survives agent restart.
- Board specs **4/4** · agent suite **22/22**. Restore point unchanged.

### R14 · v725 — run #3: Haiku slower live → Sonnet default + combat-pause filter
- **Live #3 observation:** Haiku warm **13–16s** vs prior Sonnet **6–10s** (opposite of plan).
  43 honest-empty gameplay settles burned budget on combat pauses.
- **Default flip:** `TV_MODEL=sonnet` (haiku opt-in). Gap 8→6s. Empty gameplay/town →
  **20s cool** so stands don’t re-fire vision. Warm re-proof: sonnet ready in **3s**.

### R15 · v726 — kill empty-gameplay 20s cool (Konyo: makes pile stops feel dead)
- The cool was thrash control for combat freezes, but it **blocked** the next settle after any
  empty — including “I just stopped on loot / opened inv.” Play latency > empty thrift.
- **Removed.** Only same-view skip + MIN_GAP 6s remain.

### R16 · v729 — LOOT LIFECYCLE v2 object permanence (run #3 design → code)
- **BASELINE** first inv/stash snapshot · never re-tally those names
- **SEEN** floor ledger · **GONE** same-area miss (1-read grace) = candidate only
- **CONFIRM** inv/stash + not baseline → `farmed_names` + engines/vault (tag `seen→gone→inventory`)
- **Honesty:** GONE alone never applies · inv-only still works · anchors (Cube/tomes) hold apply if missing+low conf
- Board applies **only** `farmed_names`. Suite **30/30**.

### R17 · v730 — post-run #4 tune (Grok from live state.json)
- **Bug:** first inv baselined Blade Bow/Crown → `farmed_names=[]` (Claude expected vault tags).
  Soft first panel: farm non-junk once, then lock baseline.
- **Junk filter:** potions/arrows never auto-vault.
- **Speed:** shorter vision prompt (inv was 25.8s). Anchors confirmed legible live.

### R23 · v740 — FAREWELL READ (run #7: end-of-session stash lost to shutdown race)
- On Ctrl-C / `tvd stop` (SIGTERM): one last capture + deep read → publish with `farewell:true`.
- Bypasses settle/gap. `tvd stop` waits ≤90s. End-of-run garbage stash still lands.

### R22 · v738 — CHAIN VAULT (run #4: Colossus Crossbow + Jewel)
- Stash no longer panel-greedy. Commit only SEEN / HOLDING / gone-candidate.
- Never vault Unidentified. Blood Shield class → `stash-no-chain`.
- Unit: floor Crossbow+pots → stash panel noise + Crossbow → only Crossbow vaults;
  Jewel vaults only if floor-SEEN first.

### R21 · v735 — PER-READ FRAME HISTORY (Konyo: eyes on what the AI saw)
- Archive each settle as ~1920 JPEG · `frameId` on every read · hist thumb · fullscreen lightbox.
- `GET /frame?id=n_ts` · prune last 80 · agent offline → thumb says “frame offline”.
- Also: offline empty copy uses `tvd`; history scrub of OCR NO-DB garble notes.

### R20 · v734 — STASH-TAB AUTO-INTAKE (Konyo: give the photo to the system already perfected)
- Deep `scene=stash` + `stashTab∈{runes,gems,materials}` → `GET /frame` → locked
  `runeIntake`/`gemIntake`/`materialIntake` (same as 📸 quick-upload).
- Once per stash-visit per tab · personal/shared never tally · OCR never fires.
- Live verify: stand on Runes tab with `tvd` + bible 📺 ON.

### R19 · v732 — OCR FAST LANE (Konyo: 0.1–0.2s pile→chip)
- Honest floor: true 1ms OCR of a game frame is not physics-real; **warm local Vision
  hits ~10–50ms** (bench 27ms worker). Board poll was the real lag (2s) → **250ms**.
- Dual lane: `ocr_mac --worker` → provisional ⚡ocr chips (review-first, no vault) →
  Claude deep upgrades (area/scene/verify + commitment vault rules).
- Windows later: WinRT OCR sibling. Disable: `TV_OCR=0`.

### R18 · v731 — commitment vault (Konyo: ID→throw must NOT vault)
- **HOLDING** on inv glimpse (⏳ chip) — NOT vault.
- **VAULT** only after ~30s still held (`HOLD_MS`) **or** town **stash** panel.
- **THROW-OUT** when item reappears on floor: cancel pending; reverse mistaken vault
  (`tvVaultUnregister` + unvault_names).
- Board: `vault_names` only auto-apply; belt register every committed name into owned.
- Honest badges: HIT = DB match · ⏳ hold · 🏦 vault · 🗑 throw. Suite **30/30**.

### Explicit non-goals (unchanged)
- No forge rewrite · no fabricated names · don’t loosen settle · don’t rewire vault intake photos.

### R2 · v712 — stub solid + board TDD + build-stamp sync ✅ (Grok P0-1 ✅ · P0-2 was stale-scan, origin already current ✅ · P0-3 ✅ · P1-5/6/7/8 ✅ · P2-9/10 ✅)
- `tv/stub_manifest.json` COMMITTED (P0-1) — plus the test that used to `os.remove` it now backs-up/restores (a TDD catch on the tests themselves).
- Agent suite → **12/12**: + `_readable_frame` conversion (honest both-ways: jpg-smaller or clean passthrough) · event-kind contract {boot,settle,read,skip,cap} · stub e2e (manifest → claude_read → state).
- Agent hardening: `ev("cap")` on empty-JSON parses (P1-8 — a hang can never again be silent) · pulse resumes the instant a read returns (P2-9 — CRT never sticks on 🧠 READING) · one-time `vision transport OK — read.jpg NNKB` brain line (P2-10).
- **Board TDD (the R2 core): `tests/v712_tv_board.spec.ts` — mock bridge via page.route, zero agent.** 2/2 green: CRT off→live→offline with dual-switch sync + meters + brain log; all 5 route kinds chip correctly; review-first proven (nothing applied until ✓); apply-all mutates the REAL engines (Ist 0→1, Perfect Ruby 0→1, Harlequin Crest ticked).
- `D2R_BUILD`/title/meta → v712 (P0-3). P0-4 (live re-test, bare Terminal) remains Konyo's move.

### R3+R4 · v713 — PERSISTENT VISION WORKER (the speed fix) + latency meters ✅
- One long-lived claude session (stream-json in/out): each frame = a TURN, not a cold start.
  Context-bloat guard: worker self-restarts every 8 turns. ANY wobble (timeout · dead stream ·
  junk output) kills the worker and falls back to the one-shot path — never a wedged reuse.
- `TV_CLAUDE_BIN` seam + `tv/fake_claude.py` (speaks stream-json; modes ok/slow/junk) →
  suite now **16/16**: multi-turn SAME-PID reuse · restart-after-max-turns · timeout-kill
  returns None (fallback proven) · junk parses to None (fallback proven).
- Read latency measured per read (`ms` on the record) → board READS meter shows `n / 120 · Xs avg`.
- Expected live effect: reads land in ~2-10s warm (vs 180s hangs run #1, ~15-30s one-shot cold).

### R5 · v714 — Grok's shape + robustness ✅ (P0-1 stale-scan: v713 WAS pushed · P0-2 ✅ stamp v714 · P1-4 ✅ · P1-5 ✅ · P1-6 ✅ · P2-8 ✅)
- Board spec extended: latency meter (`4.2s avg`) + cap events visible in the brain log — failures can never be silent on the board. 2/2 green.
- **Boot warm-up turn (Grok P2-8)**: the worker fires a tiny turn at launch → `vision warm — session ready in Ns` brain line; the first loot pause is never the cold start.
- Robustness: port-in-use → one clear line + exit (merged with Desktop's parallel guard — we collided mid-file and merged to one) · suspiciously-tiny capture → screen-recording-permission hint (once).
- README carries a "Last live verdict" section from now on.
- Note for Grok's scanner: two rounds in a row your "unpushed" flag was seconds stale — trust `git ls-remote` over cached scans.

### R6 · v715 — THE TZ WELD ✅
- TZ SEEN meter now cross-checks the SCREEN's purple list against the TRACKER's live rotation
  (`window._tzPeek`): agreement = `✓ tracker agrees` (two independent sources), disagreement shown
  honestly (`· tracker: <zone>`), no data = no claim. Board spec asserts the weld (stubbed _tzPeek).

### R7 · v716 — SESSION DIGEST → the cockpit 📓 log ✅
- Turning the TV off (or the agent dying) flushes one honest line into the Session log:
  `📺 TV session: N reads · M applied · Area → Area`. E2E-verified headless (mock reads → apply →
  toggle off → line present in d2r_sessionLog through LSR, account-forked like the rest of the log).

### R8 · v717 — CI for the agent suite ✅
- `.github/workflows/tv-tests.yml`: every tv/** push runs the 16-test suite on ubuntu in seconds
  (sips-less linux exercises the honest passthrough branch; fake_claude exec bit locked in git).

### R10 · v718 — Grok's end-of-night picks ✅ (formal consult, full text in the session)
- **Legibility**: every read event now carries its transport — `[warm 3.2s]` / `[oneshot 14s]` —
  and read records carry `mode`; a session's health is readable off the brain log alone.
- **Auto re-warm**: a worker death fires a debounced background warm turn — one-shot is a bridge,
  never the new normal (`vision re-warmed in Ns — back to fast reads`).
- Pick #3 (hold applies on empty/TZ-disagree) = already the design: applies are review-first ✓-only.
- **THE ONE REMAINING GATE IS HUMAN**: Konyo's bare-terminal live re-run — expect boot → warm-in-Ns
  → warm reads 2–10s. Everything else tonight is engineering-complete per Grok's verdict.

## Night tally
v710.6 · v710.6b · v711 · v712 · v713 · v714 · v715 · v716 · v717 · v718 = **10 shipped versions**,
every one gated (agent suite grew 0→16 · board specs 0→2 rich locks · CI job live) — rinse-and-repeated
with Grok co-piloting in this file throughout.

## 🏁 GATE PASSED — 2026-07-16 evening (live, Konyo's machine, his subscription)
`AGENT BOOTED → vision warm — session ready in 3s → [warm 10.4s] honest empty →`
`inventory · Superior Dagger | Light Healing Potion | Hard Leather Armor | … [warm 6.2s]`
Full pipeline proven in production: capture → settle → JPEG → warm session → scene + names →
bridge → board → route chips. Three root causes across two live runs, all fixed and shipped:
transport (v710.6, Fable) · MCP stalls (v719.1, Fable) · **API-key-over-login auth (v720, GROK
— his catch, his code, Fable gated 18/18)**. The pingpong triangle delivered.

### R11 · v721 — chips join the DATABASE + HD art ✅ (Konyo, live during his first real session)
- Every signal-feed chip now carries `data-arttip` (the bible's universal hover card — odds ·
  bases · rarity) and `artUrl()` HD art with the in-game look. Runes resolve as '<X> Rune',
  base-suffixes stripped for uniques. Board spec still 2/2; screenshot-verified.

### R12 · v722 — LATENCY RETUNE (Konyo's live feedback: floor pile read ~1min late)
- Honest diagnosis: eyes were never the lag — the 20s READ COOLDOWN stacking with ~7s vision was.
- POLL_S 0.5→0.25s (his ask, cheap) · **MIN_GAP_S 20→8s (the real lever)** · SESSION_CAP 120→240
  (same discipline, sized for the cadence) · cap published in /state, meter reads it dynamically.
- Expected feel: pause-on-pile → chip in ~10-16s worst case (was up to ~60s when gaps stacked).
- Floor-vs-inventory is already distinguished per read (scene chip ⚔️ loot vs 🎒 inventory).

### Live evidence — run #3b misread (2026-07-16 ~21:2x)
- `inventory · Hazade [sonnet 6.1s]` — **Hazade is the mercenary/party name from the top-left
  HP bars, not an item.** Prompt guard needed: party/merc/monster names from HP bars are NEVER
  items. (Also pairs with the earlier waypoint-label-in-names miss — same class: non-item UI
  text leaking into names.) Evidence-only bullet; fix rides the next prompt round.

### R14 · v733 — Fable's gate on Grok's v724-732 wave ✅
- Gates: py+html syntax ✓ · agent suite ✓ · board specs 6/6 ✓ (incl. two new locks) · code review ✓.
- **OCR HONESTY GATE shipped** (the live chat-spam evidence): OCR-lane strings only chip when
  vocab-matched — garble is dropped, never rendered; deep-lane notes stay. Spec-locked with the
  actual garbled strings from the live session.
- v723 spec recal'd to v731 semantics (auto-commit = agent vault_names only, never inv glimpse).
- `tv/ocr_mac.swift` SOURCE committed alongside the binary (public-repo provenance).
- Backlogged from Konyo live: STASH-TAB AUTO-INTAKE (frame → the LOCKED intake via GET /frame).

### R15 · v736 — UX HARDENING (Konyo live report: frozen scrollbars + phantom routing) ✅
- **ROOT CAUSE 1 (Fable's own)**: the original receiver's `|| true` made render() unconditional —
  harmless at 2s, a 4×/sec innerHTML shredder once Grok's 250ms poll landed. Now: fingerprint-skip
  (paint ONLY when the feed changed) + scroll-preserve on both containers + brain-log autoscroll
  only when already pinned at bottom. THE BOARD WORKS IN THE BACKGROUND, NEVER AGAINST THE HANDS.
- **ROOT CAUSE 2 (Fable's own, v721)**: chip data-arttip joined the GLOBAL click delegate which
  ROUTES to item pages — clicks near chips silently navigated. CLICK CONTAINMENT: bubble-phase
  stop on the feed containers; hover cards stay, TVD never routes. Doctrine: observer surface.
- **VISIBLE LIFECYCLE**: every chip wears its state (⚡ocr pulse · ⏳ holding · 🏦 vault+mule name ·
  🗑 thrown strike-through · ✓ confirmed) + row lane badges (⚡ INSTANT / 🧠 model+seconds) +
  intent left-borders (seen=blue · farmed=green). One glance = the item's whole story.
- Board suite 8/8 (incl. Grok's v735 lightbox spec).

### R16 · v737 — MCP user-experience pass (Fable drove Konyo's real browser) ✅
- **Frame history OUTLIVES the agent**: thumbs + lightbox now fall back to the archived
  `tv/frames/hist/*.jpg` the page's own server reaches — proven live (dead bridge → 1920px frame
  loaded from disk). "frame offline" only when both paths fail.
- **The phantom router unmasked**: Konyo's own v680 'always land home on reload' rule was yanking
  him off #tvd mid-session. Reconciled: TV switch ON + #tvd = a live session, honored; v680 stands
  everywhere else. (v735.1 had already fixed the intake steal — this was the remaining path.)
- **The 'black page' closed as artifact**: background-tab screenshots capture html.z-bg (animations
  paused at dark frames) + document.hidden=true — correct behavior, not a user-facing bug.
- Board suite 8/8 after every change. NEW: `.claude/agents/code-reviewer.md` +
  `.claude/agents/visual-coding-architect.md` — the repo's own review/design subagents, loaded
  with the doctrines + the actually-shipped bug classes.

## 🏁 RUN #4 — the full upgraded stack, live (2026-07-17 early AM)
✅ stash scene + anchors (Cube/TP Tome) · ✅ **materials STASH-INTAKE fired live** (frame → the
locked tally, zero clicks — the last designed feature proven) · ✅ waypoint board read as area
intel · ✅ clean pile reads 5.6–8.1s deep (Black Marsh: Colossus Crossbow spotted as a real elite
base) · ✅ **lifecycle full loop: Blood Shield + Compendium auto-committed 🏦2 at the stash
moment** (v731 semantics live) · ✅ OCR garble stayed agent-side — the board's honesty gate held.
⏳ Still to observe live: runes/gems tab intake (materials proved the mechanism) · an in-game
OCR vocab-HIT (deep lane kept winning the race this run — a good problem).

### R17 · v739 — THE VAULT MIRROR (Konyo: '3-4 runs of stashed items not reaching the Vault Manager') ✅
- **Root cause, simulated + proven**: two invisibility classes. (1) Socketed bases with a sealed
  Chronicle → suggestMule says __throwout → the old branch SILENTLY DROPPED them from the vault.
  (2) RotW custom names (Blood Shield, Compendium) had no entry in the vault's item universe.
- **The doctrine shift**: THE VAULT IS A MIRROR, NOT AN OPINION. Physically stashed = registered +
  visible, period. Throw-out verdicts become the 🗑 review-bucket TAG with the planner's why as
  advice; unknown names get a minimal EXTRA_ITEMS reference entry (universe guarantee).
- Full-flow sim (mock read → receiver → register → Vault UI): unique ✓ · 5os base ✓ · RotW ✓ ·
  rune ×1 (dedupe honest — earlier ×7 scare was the mock minting fresh timestamps). Spec-locked.

## RUN #4b — vault-mirror verification (2026-07-17 ~03:00)
✅ Nagelring: floor → held → stash → 🏦 commit fired (unique path) · ✅ vendored Damaged War Axe
correctly NEVER vaulted (stash-only counting doing its job) · ✅ holding reads (Horned Helm ·
Linked Mail · Long War Bow) · ✅ cow-level piles 12.7s · ✅ OCR noise stayed agent-side.
⏳ Konyo's eyeball verdict on the mule manager pending (v739 mirror shipped mid-run — a fresh
page load carries it).

## RUN #5 — Chaos farm (2026-07-17 ~03:30)
✅ Chaos Sanctuary area-tracked · piles 6.0-6.4s deep · holding reads (Breast Plate · Gladius ·
Diamond Bow) · materials STASH-INTAKE re-fired on the post-run stash visit (per-visit debounce
correct). No uniques dropped (RNG, not the scanner). System is routine now — runs just work.

## RUN #6 — Baal run (2026-07-17 ~04:00)
✅ Full run narrated: Throne of Destruction piles (6.3-8.1s) → 👑 Worldstone Chamber drop read
(Barbed Shield · Legendary Mallet · Flawless Diamond · Small Charm) → pickup (holding) →
stash return + materials auto-tally. Area tracking followed the whole route. Six live runs:
the scanner is a daily-driver now.

## RUN #8 — Terrorized Durance / Mephisto (2026-07-17 ~04:50) 🏆🏆
The night's crown: OCR caught the red ENTERING banner (TERRORIZED Durance L2), then the pile —
**The Face of Horror (unique) + Civerb's Ward (set) in ONE drop** [deep 12.8s]. Chronicle ticked
the unique · set tracker registered the Ward (Civerb's now 3/3 pieces). Vault filing pending the
farewell-read fix (agent closed before a stash read — third occurrence, spec already queued).
Konyo: "i was doing mephisto runs and it noticed them ausome!" — the product statement.

### 🌙 NIGHT R1 · v741 — lightbox surgery + known-dead frames + THE SYNAPSE ✅
- **Lightbox, both live bugs fixed**: (a) fullscreen was trapped by ancestor containment (the
  v512 forge-legend lesson — fixed overlays live on document.body, moved on open); (b) the
  archive-fallback flag stuck on the reused <img> — only the FIRST opened frame ever fell back;
  now resets per open with one clean chain: bridge → archive → honest missing.
- **KNOWN-DEAD FRAMES (Konyo: 'the loading photo is always the same — recognize it')**: an empty
  deep read teaches the agent that frame's signature (cap 8); a re-match is recognized locally in
  ~0ms — no vision spent, history registers an honest ⏳ transition row. 4 new agent tests (46/46).
- **THE SYNAPSE**: the brain log reborn as a thought-spine — typed glowing orbs (⚡pulse 👁sense
  📦result ⏳transition ⛔fault), newest = the active thought (enlarged, breathing), verb-first
  grammar, timestamps ghosted right. Screenshot-verified. Gated: board 9/9 + agent 46/46.
- Grok's v740 farewell read GATED ✓ (suite includes his farewell tests — the run-#7 gap is closed).

### 🌙 NIGHT R2+R3 — MCP user pass + vault e2e ✅
- R2 (Konyo's real tab, v741): all 13 history frames render ✓ · true fullscreen ✓ (the earlier
  'not full' remainder was an 11px scrollbar-naive audit check, not the app) · LIVE(0=agent off)/
  LAST(13) toggle ✓ · Esc closes lightbox ✓ · chip hover-cards wired ✓ · switch keyboard-access ✓.
- R3 (headless full-session e2e): floor/holding commits NOTHING (his doctrine) → stash commit =
  vaulted + Vault-Manager-visible + Chronicle ✓ → dropped-back = tvVaultUnregister full reversal ✓.

### 🌙 NIGHT R4 · v742 — Grok's picks: Esc stack discipline + persistent learning ✅
- **Esc stack**: the lightbox's Escape now acts ONLY when it is the visible top layer, consumes
  the event (capture phase) — vault fullscreen / search underneath never close in the same press.
- **Known-dead persistence**: learned transition frames survive restarts (tv/known_frames.json,
  gitignored) — the loading screen is learned ONCE, ever; boot announces '<N> learned frames loaded'.
- Gates: agent 46/46 · board 9/9 · html clean.

### 🌙 NIGHT R5 · v743 — synapse burst readability ✅
- Identical repeated thoughts collapse into one node with an amber ×N counter (skip-storms =
  one quiet line; the active thought stays unmistakable under any burst). Board 9/9.

## 🌙 NIGHT TALLY (Konyo's all-night TV-D order — dawn report)
v741 lightbox surgery + known-dead learning + THE SYNAPSE · R2 MCP user pass green on his real
tab · R3 vault e2e green (hold→commit→unvault) · v742 Esc stack + persistent learning (Grok's
picks) · v743 burst collapse. Suites: agent 46/46 · board 9/9 · every round shipped + gated.
Grok's verdict pre-dawn: "you're past the hard ships."

### 🌅 DAWN R6 · v744 — THE CINEMA ARC (Grok's dawn audit, all 3 ordered by Konyo) ✅
- **CRT FACE (Grok #1 — 'the TV shows what the AI sees')**: the live /frame now breathes inside
  the TV bezel under the scanline (4s throttle — no fetch storms), click = fullscreen LIVE view.
  The 👁 placeholder retires whenever a real face is on screen.
- **THE RUN STORY (Grok #2)**: the session as a film strip above SIGNAL FEED — 🗺 area chapters ·
  ⚔️ seen · 🎒 held · 🏦 vaulted · 🗑 tossed · ⏳ transitions, built from the SAME persisted reads
  the history shows (schema-true: items[].kind/key/label + vault/pending/thrown_names). Click any
  tick → the matching history row scrolls in and pulses. Repeated identical ticks collapse so a
  long Meph night stays one readable reel. Verified LIVE on Konyo's real Durance session:
  🗺 Durance of Hate Level 2 → ⚔️ 2 seen, click-jump pulsed read #5.
- **FRICTION CALM (Grok's list)**: honest tab copy (terminal `tvd` → flip the switch) · NO DB →
  quiet `base` badge (ordinary gear isn't an alarm) · apply-all = quiet text action · 30px chip
  trophies · history clears the dock · ghost frame placeholders · ONE primary meter (MOTION).
- Gates: board **10/10** (new v744 RUN STORY spec — seeded with the true persisted schema after
  the first seed's `name` vs `key/label` lie surfaced as 'undefined' in a row) · agent **46/46** ·
  html clean · headless screenshots verified · Fable code-reviewer pass on the diff.

### 🌅 DAWN R7 · v745 — the story never goes dark (Konyo: "i dont see any changes... session
### history timelined with that same logic?") ✅
- **The v744 reel was honest to a fault**: it followed the LIVE/LAST toggle, and with the agent
  off the default LIVE view is empty — so the strip hid and the whole arc looked invisible.
- **v745 fallback**: when LIVE has no story, the reel narrates the newest ARCHIVED session,
  capped `📼 RUN STORY · LAST SESSION` — it introduces itself now. Clicking a tick on a fallback
  reel flips history to LAST first, then jumps + pulses the row.
- **The history list is storylined with the same logic**: 🗺 chapter divider rows wherever the
  area changes — a Meph night reads Town → Durance → Chaos as chapters, not a flat list.
- Verified on Konyo's real tab: default view shows the capped reel, click flipped live→last and
  pulsed read #5, chapter divider rendered. Gates: board 10/10 (spec extended: fallback cap +
  chapter locks) · agent 46/46 · html clean.

### 🌅 DAWN R8 · v746 — ⏳ ENTERING, pinpoint (Konyo: "this photo is ENTERING a PORTAL or
### ENTERING A NEW GAME, depending on the photos beforehand") ✅
- **THE REAL BUG**: `known_dead_match` was defined (v741) but NEVER CALLED — lost in a parallel-
  edit merge. The agent learned the portal frame and then paid 7.2s of Sonnet on it anyway
  (his read #2). Now wired into the live loop: a learned frame is recognized locally, publishes
  an honest ⏳ transition read at 0ms, and consumes zero vision.
- **The label reads the story so far**: LAST_AREA rides every deep read — the portal frame says
  "through the portal — leaving Durance of Hate Level 2"; with no prior reads it says "entering
  a new game"; otherwise "loading — next area coming". Proven by driving the REAL main loop:
  pre-learned frame → `⏳ through the portal — leaving Durance of Hate Level 2 [known frame · 0ms]`.
- **Sonnet can say it too**: the vision prompt gains scene `transition` (burning portal art /
  act loading screen / dark no-HUD frame) — and an empty transition read ALSO teaches the local
  cache (should_learn_dead covers gameplay + unknown + transition).
- **The board stops shrugging**: transition reads render `⏳ ENTERING — through the portal —
  leaving <area>` in the feed AND history (never "nothing readable"), the where-line carries ⏳,
  and the story reel's ⏳ tick says "portal" when it knows the from-area.
- Gates: agent **49/49** (transition_note context · should_learn_dead · prompt vocabulary) ·
  board **10/10** (transition-honesty locks) · real-loop e2e proof · his known_frames.json intact.

### 📡 R9 · v747 — NOW ON AIR: the Live Chapter stage (Grok's design, Konyo: "ship NOW stage —
### flagship, subagents, TDD, pingpong after") ✅
- Built by the Fable **visual-coding-architect** subagent, TDD-first; audited by the Fable
  **code-reviewer** subagent (verdict SHIP, all 8 recurring bug classes clean).
- **P0 THE STAGE**: full-width live chapter card between the CRT hero and THE RUN STORY. Only
  exists while LIVE (CRT static owns the off story). NOW ON AIR ● + read #N (synapse-synced),
  per-scene skin (loot cold-blue · inventory gold · stash purple · town camp · transition amber),
  big 🗺 area line, caption = area + scene + intent ("Durance of Hate Level 2 · floor loot ·
  eyes open") — never just an item list.
- **P1 THE CAST**: one HD-art tile per resolved name — rarity ring (unique gold · set green ·
  rune orange), lifecycle truth on the art (⚡ocr shimmer → ✓deep solid · ⏳hold breathing ring ·
  🏦 vault green seal · 🗑 struck grey). READING… = type-on caption + ghost silhouettes. Honesty
  gate: notes/garble never cast.
- **P2 THE SCENARIO**: boss portrait chip when the area is a boss house (Meph/Baal/Diablo/Andy/
  Duriel/Nihlathak/Summoner/Countess, tight regexes) · 🔥 purple terror tick when tz[] agrees.
- **P3 ONE STORY LANGUAGE**: stage rides the same read # as the SYNAPSE; the same truth flows on
  into the reel + history untouched.
- **Latent v746 gap fixed** (architect's catch): live FEED entries never carried note/
  transition_from — the portal note only worked from persisted history. Now consistent live.
- Gates: board **11/11** (new NOW-stage lock: hidden-off · cast honesty · lifecycle rings ·
  portal wash · read-# sync) · agent 49/49 · reviewer nit folded (fp commits only after a
  successful render) · 4-state screenshots verified.

### 🏓 R10 · v748–v750 — Grok's post-ship critique, all three implemented ✅
Grok's verdict on shipped v747: "Ships the design… v747.1 plate polish > original sketch. Name/
continuity discipline < sketch." His TOP 3, each TDD-locked:
- **v748 CAST = CREDITS**: 66px mid-token ellipsis killed the names ("Harlequin_"). Tiles now
  autosize to 96px, names wrap 2 lines, runes stay short — spec asserts the FULL "Harlequin
  Crest" renders.
- **v749 CHAPTER CAST MEMORY**: the stage narrated the last packet, not the chapter. Now the
  cast is the union of honest routes seen in the current area (cap 12, latest lifecycle per name
  wins — thrown>vault>hold>conf>ocr), cleared on area change. Spec: empty gameplay read keeps
  the pile on stage; area change starts a fresh cast. Never invents — only prior honest routes.
- **v750 THE PORTAL KEEPS THE CHROME**: transitions dropped Mephisto + terror mid-chapter and
  stacked three ⏳. Boss/tz now resolve from transition_from/chapter memory, ONE hourglass
  (ENTERING flare folded), and the chapter cast dims to ghosts under the wash. Spec: leaving
  Durance keeps the Mephisto chip; exactly 1 ⏳ on stage.
- Gates: board **11/11** (all three locks folded into the NOW-stage spec) · screenshots verified
  (portal frame: chrome survives, reel continues the same story language below).

## GROK INSIGHTS (R10, verbatim picks)
- "Cast as readable trophies — 66px ellipsis murders names" → credits discipline.
- "Stage is 'latest packet', not 'this chapter'" → chapter cast memory, lifecycle-latest-wins.
- "Story identity blinks off mid-Meph" → context chrome through transitions, display-only,
  never fabricated.
- Reading-state ghosts "read as empty/broken, not scanning" — queued for a later polish round.

### 🏓 R10 VERIFY (Grok, post-ship) ✅
All three gates PASS on the shipped code + screenshot: "R10 v748–v750 SHIP — all three Grok asks
TDD-locked; portal chrome holds Meph + terror with one hourglass." No honesty or render-doctrine
violations. Noted nits (non-blocking, queued): lifecycle merge is last-write not priority-merge ·
hold-⏳ could stack with the portal ⏳ if you portal mid-hold · credits emoji-strip assumes
route() labels. Next-session queue: reading-ghosts polish only.

### 🎬 R11 · v751 — THE HERO BAND (visual-coding-architect's autonomous polish pass) ✅
- The architect ran its own visual pingpong (Grok CLI third-eye) and shipped the stage as a
  **full-bleed broadcast lower-third**: edge-to-edge CRT grimoire plate (scanlines + vignette +
  gold hairlines), serif display headline (🗺 DURANCE OF HATE LEVEL 2), pulsing on-air bug,
  jeweled boss/terror pills, LIVE CAST strip label, phosphor vault glow, portal ENTERING flare,
  dashed-gold reading ghosts w/ teleprompter caret.
- Verified before ship: my v748–v750 work fully intact underneath · board 11/11 · renderer emits
  the .tvn-content column the CSS expects · geometry probed: the 337px horizontal overflow
  predates this pass (exists on v750) — the new html{overflow-x:clip} guard actually contains
  that latent quirk; inner scroll rails unaffected.
- ⚠️ OPS: the Grok MCP XAI_API_KEY is DEAD (rotated/expired) — both pingpong rounds tonight ran
  through the signed-in Grok CLI instead. Rotate the key at console.x.ai to restore the MCP path.

### 📼 R12 · v752+v753 — REPLAY + the full-audit agent batch (Grok audit, Konyo: "implement all,
### ship end to end") ✅
- **v752 📼 REPLAY**: `tvd sim` (canned demo) · `tvd replay` (--list/--n/--pace/--exit-after) —
  re-runs a REAL past session: the frames the agent archived + the reads it recorded drip
  through the REAL loop (TV_STUB manifest seam + TV_FRAMES_DIR watch seam). Persistent journal
  tv/sessions.jsonl (gitignored, newline-safe, 4MB rotation), seeded with his 97 frame-backed
  reads from the browser history — `tvd replay --n 1` re-broadcasts the 03:18 Meph run incl. the
  Civerb's Ward + Face of Horror double-grail read. Honesty: replay never journals itself
  (TV_NO_JOURNAL), never OCRs replayed pixels (TV_OCR=0), only replays frames that still exist.
- **v753 audit batch**: ONE version truth (VERSION const → banner/HUD/state; the v740 stale
  stamps are gone) · frame archive 1920→2560px, keep 80→600 + 500MB disk ceiling (the pruner was
  silently eating his photos — the "not openable" class) · farewell can never hang (capture hard
  timeout → read.jpg → newest archived frame fallback chain) · run-#8 fix: gameplay+names =
  loot-class for the lifecycle (grail piles enter the SEEN chain) · journal lane field · watch
  mode accepts .jpg (never re-eats read.jpg) · journal-write failure surfaces once · tests never
  touch the real journal · TRACKING refreshed (runs #4–8 + cinema arc closed, TV-B26 opened).
- Gates: agent **55/55** (lifecycle-class + replay manifest + journal + seam locks) · replay
  e2e proven on the real Meph session · board pass (v754) running with the architect.

### 🪟 R13 · v755 — THE COUSIN MOVE: one-line Windows install ✅
- **`irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex`** — one paste: winget-installs Git +
  Python + Claude Code (Anthropic's official installer) if missing, clones/updates the public
  repo, drops a "TV DIABLO" Desktop shortcut. The ONE human step that can never be skipped:
  the cousin's own Claude login — the shortcut's first run walks him through it (opens claude,
  waits for credentials, verifies). His subscription, his limits, zero API keys.
- **tv/start_tvd_win.ps1** (the shortcut): strips API-key env (the v720 lesson, Windows
  edition) · pull-first · starts capture_win.ps1 minimized + the reader --watch in one window ·
  Ctrl-C stops both, farewell read included.
- **Serving**: deploy.sh copies the installer into the dist scaffold; functions/_middleware.js
  exempts exactly /d2r/install-tvd.ps1 from the password gate (zero secrets in the file — it's
  in the PUBLIC repo anyway; everything else stays gated).

### 🛠 R14 · v758 — the v754 board pass lands complete (all 8 audit items + Konyo's routines fix) ✅
- Items 1–6 (badge identity · scanning ghosts · light thumbs · mobile hero band 760+640 ·
  TV-B7 chip→card ↗ affordances with scoped listeners · overflow ROOT CAUSE = .tvd-switch
  stretched by column-flex then ×1.35 scaled → align-self:flex-start) shipped inside v757's
  absorb; verified intact marker-by-marker.
- **Item 7 — THE ROUTINES JUMP, root-caused** (Konyo: "all the routines are jumping"): the
  60s status counter ('status…' → 'N/M fires today') was the ONLY variable width in a
  right-anchored fixed pill — every refresh shoved the whole G–T strip leftward. Plus TWO
  warring !important right-offsets broke narrow screens. Fixed at source: one clean dock rule
  (dock-aware bottom, tray-clearing right, responsive max-width), counter locked to 150px
  tabular-nums (124px @760), the !important pair removed. Strip position now CONSTANT across
  all status texts at 1440 + 720, on TVD and lore tabs.
- **Item 8 — CI flake killed**: the stage test's toggle-OFF assert now condition-waits
  (waitForFunction, 5s) instead of racing a 300ms sleep; same sweep applied to the new tests.
- Gates: board **13/13** · agent 55/55 · html clean · D2R_BUILD → v758 (badge stays honest).

### 🎛 R15 · v759 — the CONTROL CONSOLE goes broadcast (Konyo: "stretched and full screen…
### breathing… really feel full screen… upgrade any HD art") ✅
- Grok's v757 control app UI (a centered dialog floating in void) rebuilt by the Fable
  visual-coding-architect + finished/gated by the session: a TRUE fullscreen broadcast face —
  100dvh grid (header · stage · console rail · AGENT MIND ticker · footer), everything clamp()-
  fluid so it breathes at any size.
- **THE STAGE**: giant serif phase title (STANDBY/SIMULATION/LIVE) with state-tinted glow ·
  Diablo silhouette from the HD art DB floating/breathing behind it (ember halo, state-colored) ·
  drifting scanlines + soft CRT sweep + vignette pulse · broadcast lower-third meters
  (MODE/READS/AREA/SCENE) · REC marquee.
- **THE CONSOLE RAIL**: five big action cards (ON AIR / OFF / STOP / RESTART / SIM) with state
  rings — the active mode literally glows · bridge/model signal panel with a live bar · board +
  log utilities. Keyboard: Space = on/off, L = log.
- **HD art route**: GET /art/<name> on the control server — read-only, realpath-checked inside
  art/, mime whitelist (traversal probe → 404, verified). Emblem = Ohm rune, hero = Diablo.
- Verify pass caught: a STALE control server holding :17772 made the art route look 404 and the
  footer look v757 (kill-then-test lesson) · ver payload/banner/footer all stamped v759.
- Gates: py ast clean · art route 200 + traversal blocked · screenshots at 2000/1440/1280 LOOKED
  at · board suite untouched (13/13 at v758.1) · agent 55/55 untouched.

### 🪟 R16 · v760+v760.1 — the Windows twin, verified (third-eye supervision) ✅
- **Grok's v760**: control app goes cross-platform — netstat port detection · CREATE_NO_WINDOW/
  CREATE_NEW_PROCESS_GROUP hidden spawns · capture_win.ps1 auto-started/stopped with the agent ·
  --watch on Windows · installer shortcut → hidden control UI (Chrome/Edge --app kiosk) ·
  pythonw-aware Real-Python · platform + capture surfaced in the footer. 4 of the 5 pre-review
  traps covered clean.
- **Trap 2 confirmed + fixed (v760.1)**: Windows soft-stop was `taskkill` without /F — WM_CLOSE
  that a windowless console app never receives → 90s of nothing, then hard-kill = FAREWELL NEVER
  RUNS on the cousin's box (the run-#7 stash-loss class, silently reborn). Fix both sides: the
  agent now registers SIGBREAK (CTRL_BREAK arrives as SIGBREAK on Windows; SIGTERM does not
  exist there), and the control app soft-stops its OWN child via send_signal(CTRL_BREAK_EVENT)
  (it is spawned CREATE_NEW_PROCESS_GROUP), keeping taskkill only for foreign pids.
- Gates: py ast both files · agent 55/55 · Mac control server boots + /api/status healthy post-
  edit · true Windows farewell e2e = cousin's first `tvd stop` (flagged for his install run).

### 🖼 R17 · v761+v761.1 — the NATIVE SHELL, verified ✅
- **Grok's v761**: the control console opens in a REAL OS window — pywebview (WKWebView on Mac,
  Edge WebView2 on Windows), pip-installed by both installers, ensure_webview() one-shot retry
  at first launch, Chrome/Edge --app demoted to emergency fallback, --window-only attach mode
  for a second window onto a running server. Headless bare-run preserved (CI/screenshot flows
  unaffected — verified).
- **Third-eye fix (v761.1)**: PEP 668 managed pythons (Homebrew) reject even `pip --user` —
  a cousin-Mac would silently live in the browser fallback forever. Both the installer and
  ensure_webview() now retry with --break-system-packages (user-scoped GUI dep) and re-probe
  the import between attempts.
- Verified on Konyo's Mac: pywebview imports clean · headless server + /api/status healthy ·
  py ast + sh -n gates green · agent 55/55. The true native window = his next double-click.

### 🏆 R18 · v763+v764 — TV → THE CHRONICLES + the switch becomes a LAMP ✅
- **v763 CHRONICLE ROUTING** (Konyo: "route it to the beginning of our system and let the engine
  do its work"): ONE head — window.tvChronicleRoute — knocks on each engine's front door:
  uniques → toggleOwned (dated foundLog, the grailFoundUni path), set pieces → toggleSetPiece
  (setPieces + the same ledger). Suffix-tolerant canonical resolution (the grail keys are
  'Harlequin Crest (Shako)' / "Sigon's Guard (shield)" — raw names now resolve and tick the
  CANONICAL key, never a duplicate). Chronicles stay separate coding-wise. Two feeders:
  vault commits stamp the ledger LIVE (was next-boot), and the NEW chat lane — the vision
  prompt reads DISCOVERY broadcasts ('<player> has found <item>') into discovered_names:
  chronicle-only, 💬🏆 chip, NEVER vaulted (knowledge, not possession).
- **v764 AUTO-SYNC** (Konyo: "i don't need an ON/OFF button on the website — sync it to the
  app"): the board SENSES the agent — a light /ping probe every 2.5s while dark auto-engages
  the live poll the moment the app's ON/SIM starts the bridge; the poll's catch already drops
  to OFFLINE on stop. Both switches are passive LAMPS now (clicks/keys removed, honest title).
  _tvdToggle stays as the spec/manual seam; probe is webdriver-gated so specs stay deterministic.
- **SIM wrong-page bug fixed** (his repro): macOS `open` DROPS file:// fragments → the board
  landed on the wrong tab; ON/SIM also minted a new tab every press. Now: direct browser spawn
  (Chrome/Edge/Brave, fragment survives, `open` fallback) + open-once per control session —
  afterwards the already-open tab lights up by itself.
- Debug war story: a three-part edit died mid-script BEFORE its file write (assert threw) — the
  feed badge/items-flag/CSS silently missing while the ledger side worked. Re-grep-then-verify
  saved it; the DOM dump beat guessing.
- Gates: board **14/14** (new v763 chronicle lock: canonical uni+set stamps · discovery chip ·
  never-vault · idempotent re-broadcast · live vault stamp) · agent **57/57** · html clean.

### 🎞 R19 · v765 — THE THEATRE: eyes on history (Konyo: "its not really simulated anymore…
### its own independent VIEW") + the full Grok-audit batch ✅
- **THE THEATRE**: the SIM button reborn — replays REAL sessions in the app: archived frames
  full-bleed with scanline grade, caption bar (time · read # · 🗺 area · scene · name chips ·
  portal notes), beat timeline scrubber (named reads stand taller; frameless beats honest-dim),
  play/pause · 1×/2×/4× · session paginator (9 sessions deep tonight). Zero agents involved —
  pure eyes-on-history. Server: /api/sessions · /api/session?n · /hist/<id>.jpg (path-safe).
- **His two live bugs fixed**: /api/stop no longer calls open_board (the phantom window) and
  skips the 90s farewell wait for sim agents (the stuck-SIM screen); restart uses the
  open-once guard.
- **Toggle-glow buttons**: lit while their mode runs, click again = off (ON AIR toggles OFF;
  THEATRE re-click closes); STOP shows honest "farewell…" while it waits.
- **Grok-audit batch folded**: ONE version truth v765 (app payload/banner/UI footer/D2R_BUILD)
  · chronicle NEGATIVES locked (OCR garble/'Ring'/'Grand Charm' never chronicle, ledger
  byte-identical) · control_agent.log 2MB rotation · copy truth ("flip the switch" is dead —
  the board syncs itself).
- polish762's v762 interaction-depth pass (press/flash/focus rings/working states/rune jewels/
  meter tweens/brain slide-ins) verified intact underneath.
- Gates: control **7/7** (NEW tv/test_control.py: theatre endpoints on fixtures · hist traversal
  block · stop-never-opens-board · open-once) · agent 57/57 · board 14/14 · theatre verified
  LIVE on his real 9-session archive (screenshot: session 1/9 playing, lit button, clean close).

### 📺 R20 · v766 — THE WEBSITE BECOMES THE APP (Konyo: "replicate the APP in the TV-D tab") ✅
- **One product, two surfaces**: #tab-tvd rebuilt into the app's console architecture by the
  Fable architect across three correction rounds (Konyo course-corrected live from screenshots):
  header band (emblem · serif brand · clock · ON/OFF-AIR pill · 🎞 THEATRE) → the APP'S STANDBY
  HOMESCREEN as the stage (giant state-tinted serif phase word over the breathing Diablo
  silhouette, kicker/caption/marquee, meters as the lower-third INSIDE the stage, phase rides
  the live beat: SETTLING/WATCHING/READING) → LIVE runs the frame film in the same stage →
  console rail (RUN STORY + SYNAPSE·BRAIN LOG as jeweled panels) → SIGNAL FEED ticker band →
  archive below.
- **NO MORE SWITCHES** (his ask, twice): both auto-sync lamps are ON/OFF-AIR pills now — the tab
  header and the session cockpit card; the engine elements survive hidden (dual-render + 14
  specs untouched).
- **🎞 THE THEATRE on the site**: full-viewport cinema replaying d2r_tvdHist sessions — real
  frames via the bridge /frame?id= (+ tv/frames/hist fallback), pagination, play/speed, honest
  empty — "simulation mode" viewing, same player as the app.
- **GET THE APP**: flagship install cards (🖥 curl one-liner · 🪟 irm one-liner) with copy
  buttons — the cousin move is now a website feature.
- True-extracted art: uber-diablo emblem; the flaming-logo half-page misfire caught by Konyo and
  demoted to taste.
- Gates: board **14/14 UNCHANGED** + v766 locks **4/4** + smoke 8/8 (my re-run: 18/18) · html
  clean · agent suite untouched · setState className-rewrite trap caught and defused (stage class
  preserved like tvb-bigswitch).

### 🏓 R21 · v767 — Grok round 1/5 implemented (the re-ingest sleeper + version truth) ✅
- **THE SLEEPER, CONFIRMED then killed** (Grok's hypothesis, my stress-repro: 1 read → reload →
  2 rows): a hard refresh kills in-memory SEEN but not the durable d2r_tvdHist — the poll re-walks
  the agent's reads[] ring and re-mints history (and could re-knock the vault/chronicle doors).
  Fix: on the agentStart handshake, SEEN resumes from the persisted session (reload identity);
  pushHistRead gets an identity belt (frameId+n / ts+n) for the two-LIVE-tabs case. Spec locked
  (reload → still exactly 1 row). Same class as REG-019's cousin: durable-vs-memory identity.
- **ONE VERSION TRUTH**: agent VERSION · control payload/banner · UI footer fallbacks · D2R_BUILD
  all stamp v767 in one ship (Grok: "screenshots lie" — no more v753/v759/v765 drift).
- **Dead copy sweep**: every remaining "flip the switch/scanner on" phrase → lamp truth
  ("app ON · board auto-syncs"). grep flip-the-switch = 0.
- **RUN STORY lights on chapter one** (was hidden until 2 nodes — first loot now starts the reel).
- Gates: board+console **19/19** · agent 57/57 · control 7/7 · html clean.
- R1 pick #1 (film-first live stage) + Konyo's side-by-side alignment ask → the v768 architect pass.

### 🏓 R22 · v768-pre — Grok round 2/5, my half shipped (stop-race gate + lifecycle continuity) ✅
- **The stop-race gate** (Grok R2 #2): threaded stops now raise _stop_inflight — /api/on and
  /api/restart answer "farewell still finishing" instead of lying "bridge already live" at a
  dying agent; status mode reports **stopping** so the UI can dim honestly (UI half in the
  align768 round). Both stop paths clear the flag on every exit.
- **Lifecycle continuity** (Grok R2 #3 — the R1 sleeper's agent-side twin): LootLifecycle.restore()
  rehydrates seen/pending/candidates/vaulted from the last persisted snapshot when the previous
  run ended <10min ago — an OFF→ON or crash restart no longer orphans floor-proven items into
  'stash-no-chain'. Boot prints "♻ lifecycle rehydrated". Never clobbers live entries.
- Grok R2 #1 (app film wrong-origin — control :17772 has no /frame; must point at the agent
  bridge) + the UI stopping-state → folded into align768's v768 round with items 8-9.
- Gates: agent **60/60** (3 new restore locks) · control **7/7** · align768 mid-build.

### 🎯 R23 · v768 — THE ALIGNMENT SHIP (Konyo's side-by-side + his button audit + Grok R2, all in) ✅
- **PIXEL PARITY**: site TV·D = the app's exact geometry — stage right under the header (GET THE
  APP re-homed to the tab bottom), the app's clamp values verbatim (cols/gaps/radii/stage
  height), meters = the app's filled lower-third cards, SIGNAL FEED = the AGENT MIND ticker
  band, app-style micro-footer reading D2R_BUILD live. Side-by-side @2000: ONE product.
- **FILM-FIRST, both surfaces**: live + loaded frame → the giant phase word demotes to a corner
  bug, hero/caption fade, the FRAME is the star. Standby keeps the giant word.
- **KONYO'S BUTTON AUDIT closed** (matrix 22/22): ON→off routes the FAREWELL stop (was the
  no-farewell path) · ONE lit/dim mechanism (paint()-driven .lit; idle buttons truly grey-dim —
  his "glowing on, dim grey off") · mode:"stopping" → dimmed ON + FAREWELL… bug — no more
  stuck-green glow (server gate from v768-pre pairs).
- **TWO deep-link gates dead** (his "routes me to the wrong page", root-caused twice): the lamp
  change orphaned d2r_tvdOn (gate A) AND the v680 parse-time normalizer rewrote ANY bare hash →
  #tools BEFORE routers ran (gate B — #tvd literally became #tools). Explicit #tvd now lands
  TV·D unconditionally; spec-locked both directions.
- **App stage un-buried** (bonus root-cause): THE THEATRE had no [hidden] display guard — it
  permanently covered the app stage (the stuck-SIM screen). Guard added.
- **Grok R2 fully landed**: film wrong-origin fixed (agent bridge :17771, not :17772) ·
  stopping-state UI · + the v768-pre server gate & lifecycle continuity.
- Gates: board+console+smoke **28/28** (console spec now 5 incl the #tvd lock) · agent 60/60 ·
  control 7/7 · button matrix 22/22 · html clean both files.

### 🏓 R24 · v769 — Grok round 3/5: THE PARSE WAS LYING (+ theatre depth + film honesty) ✅
- **THE SLEEPER OF THE ARC** (Grok's repro, confirmed live): `_parse_read` silently killed TWO
  shipped features on the only path that matters — the scene allowlist rewrote `transition` →
  `gameplay` (v746's portal scene never minted from live vision) and `discovered` was never
  extracted (v763's chat lane: 0/116 journal rows). The tests had injected dicts PAST the parser
  — the boundary was never round-tripped. Fixed one line + one slice; 4 round-trip locks in the
  agent suite. Doctrine addition: EVERY prompt-schema field gets a parse round-trip test.
- **THEATRE = the chain, not just names**: /api/session beats now carry vault/pending/thrown/
  discovered/intent/stashTab/farewell; captions seal every name (🏦 vaulted · ⏳ held · 🗑 thrown ·
  💬🏆 discovered) on BOTH theatres; timeline beats class vaulted (mint, tall) / holding (amber) /
  named / noframe.
- **Film honesty**: a frameless beat clears the src (the app was showing the PREVIOUS photo
  under portal captions); same-frame OCR+deep pairs coalesce (richer row wins) so the reel never
  double-steps one photo.
- Copy nit: the site theatre's "in the TV DIABLO app in the TV DIABLO app" de-duplicated.
- Gates: agent **64/64** (4 new parse locks) · board+console 19/19 · control 7/7 · html clean.

### 🏓 R25 · v770 — Grok round 4/5: the twin finished for real + cousin-proofing + the thin poll ✅
- **THE SLEEPER AGAIN (same class, caught again)**: the SITE theatre's beat projection dropped
  every chain field — the R3 caption seals were dead code on the board (claim without the
  boundary). thzBeats now projects vault/pending/thrown/discovered/intent/stashTab; the seals
  fire on both surfaces for real. Two rounds, two incomplete-boundary catches: the doctrine
  (round-trip every boundary) earns its place.
- **Cousin-proofing** (Grok R4 #2): the Windows installer bootstraps the Edge WebView2 Runtime
  (pywebview's engine — locked-down PCs lack it and died silently to a browser); native-window
  failures now SHOUT (MessageBox on Windows / osascript alert on Mac, with the fix line + log
  path) instead of vanishing under pythonw.
- **The thin poll** (Grok R4 #3): /state?since=<ts> returns a delta — 4 polls/sec no longer
  parse a 200-read ring every tick inside the pywebview WebView; the board sends since=SEEN once
  warm, cold polls stay full. Long farm sessions stop paying the JSON/GC tax.
- Gates: agent **65/65** · board+console 20/20 · control 7/7 · html clean.

### 🏓 R26 · v771 — Grok round 5/5, THE CLOSER (series sealed) ✅
- **THIRD BOUNDARY STRIKE, closed**: hist entries never stored discovered_names — the site
  theatre's 💬🏆 seals were dead while the app's (journal-fed) worked. entry now carries the
  slice; the chain-truth path is whole on every surface. Three rounds, three silent breaks of
  ONE truth path — the round-trip doctrine now includes DURABLE HIST explicitly.
- **Site theatre = app theatre for real**: timeline chain classes (vaulted mint-tall / holding
  amber) + same-frame OCR+deep coalescing ported to the board (the R3 half-port finished).
- **Version identity can't drift again**: all stamps → v771 + a PARITY LOCK in the control suite
  (agent VERSION must equal the control payload ver — drift = red suite, not a screenshot lie).

## 🏆 GROK R1–R5 ARC VERDICT (capstone, verbatim)
"The product is no longer a scanner tab — it is a broadcast console with memory: live film,
object-permanence loot chain, dual-surface theatre, native Mac/Windows shell, and a board that
auto-syncs as a lamp. Strongest surfaces: the lifecycle chain (seen→hold→vault / throw-out
honesty), the cinema language (NOW stage · RUN STORY · Theatre), and the cousin install path
(one paste, subscription-only vision). Weakest surfaces: dual-film archives (d2r_tvdHist vs
sessions.jsonl) still diverge under incomplete field projection; version identity regressed
after v767 [fixed + locked this round]; the control shell is TV-complete but still hollow next
to Session/Tools/Forge/grail engines that actually hold the player's life [the 20:02 night
project]. Protect at all costs: the vault/chronicle wire — agent vault_names/discovered_names →
board engines only through tvVaultRegister/tvChronicleRoute, never a second ledger — every
incomplete boundary this arc found was a silent break of that single truth path."
## Night-project handoff flags (Grok R5, for the 20:02 arc): host/deep-link the bible engines,
## never fork them · round-trip is law incl durable hist · file:// vs https LSR origin story ·
## TV wires stay first-class · unify the two film archives before expanding the shell · stamp
## truth before screenshots.

## 🌙 NIGHT ARC — THE FIVE TABS (started 2026-07-17 20:00, Konyo's order; target ~20 versions)
### ARCHITECTURE DECISION (ledgered before code, per the workflow + Grok's handoff flags)
The app gains Session · Tools · Forge · F-Uniques · F-Sets — and per the "host, never fork"
flag, the app will NOT reimplement those engines. Decision: **THE APP HOSTS THE BOARD**:
1. The control server serves the LOCAL bible.html (and art/) same-origin at /board — one stable
   http origin for app users (kills the file:// LSR split for the app world; Konyo's own 8686
   tab stays his dev surface).
2. control_ui gains a BIBLE rail — five console-styled tabs; each opens THE ONE board window
   (v773.1 singleton) deep-linked at that tab (#session/#tools/#forge/#funi/#fsets — hash
   routing exists and is spec-locked since v768).
3. The night's real work = per-tab perfection waves: each of the five surfaces verified +
   polished INSIDE the native WebView at app geometry (fonts, dock clearance, scroll, art),
   TDD locks per tab, one version per wave, reviewer audit per ship.
4. After the build arc: SEVEN third-eye rounds (Grok CLI if its auth allows — Konyo's chat quota
   is capped; Fable reviewer rounds substitute where needed).
Wave plan: v774 /board serve + bible rail + deep-link singleton nav → v775 Session → v776 Tools
→ v777 Forge → v778 F-Uniques → v779 F-Sets → v780+ integration polish + the seven rounds.

### 🌙 N1 · v774 — THE APP HOSTS THE BOARD (night foundation) ✅
- **/board same-origin serve**: the control server serves the LOCAL bible.html (art/ + theatre
  hist fallback resolve same-origin too, traversal-blocked) — the native window now lives on ONE
  stable http origin; the file:// localStorage split is dead for the app world.
- **THE BIBLE RAIL**: five console-styled tabs in the app (⚡Session 🧰Tools 🔨Forge 🏆F·Uniques
  🧩F·Sets) — each opens THE ONE singleton board window (v773.1 pid-tracked) deep-linked at its
  tab via /api/board?tab= (whitelisted) + --hash= (rides the v768 unconditional-hash fix).
- Spec-drift honestly updated: the Grok-era lock asserting the file:// URL now asserts /board#.
- Gates: control **12/12** (3 new host locks) · py ast · ui js clean · live-verified (200 html
  w/ D2R_BUILD · hist traversal 403).
- REG-020 postscript shipped first: v773.1 singleton + v773.2 belt-sweep + orphan self-close.

### 🌙 N2 · v775 — WAVE A: THE FAMILY SPINE ✅
- ONE console header spine (tvf- namespace) across all five tabs, mirroring the TV·D tvz-head:
  emblem box · serif GOLD title (family accent unified — Forge/Fsets were green) · mono purpose
  line · real-number stat rails. TOOLS finally has a hero (🧰 + Vault/Runes/Gems live counts via
  _renderToolsSpine — no fabricated numbers). Funi/Fsets/Forge heads get the emblem treatment.
- FAB-clipped subtitles fixed with clearance (not FAB moves) · Session header/content left edges
  aligned at >1500 (both sat at 224 @1920, were 14/224 split).
- Scout thesis honored: no content rebuilds this wave — spine + consistency only.
- Gates: 71 specs green across 9 suites (board/console/smoke + the forge-family regression set) ·
  0 h-overflow, 0 console errors at 1280/1500/1920 through the SAME-ORIGIN app host (/board).

### 🌙 N3 · v776 — WAVE B: TOOLS wears the family chrome ✅
- #tools-index chip rail → console chip band (mono group labels, gold-hover chips, behavior
  untouched) · the 16 tool accordions inherit the Funi/Fsets card chrome (12px radius, per-tool
  --tc accent left-spine, hover lift) · the AI flagship keeps its hero chrome.
- Specificity fight documented: the v-old global .boss-card!important reset was silently flattening
  the v705 premium accents too — scoped Tools-local win, global cleanup left as a conscious call.
- Gates: 43 specs green (board/console/smoke + tools regression set) · computed-style verified per
  card · 0 h-overflow 1500/1280.

### 🌙 N4 · v777 — WAVE C: FORGE'S CHRONICLE SEALED (+ the 99-× bug) ✅
- **The stray × was 99 stacked bugs**: every done-row's absolute ✕ escaped its unpositioned row
  and PILED at the tab's top-right — the visible one dismissed whichever row topped the z-stack.
  Fixed at source (.f-donerow position:relative; ✕ inline static per row).
- **The triumph state** (100% only; active-forge byte-identical): ⚒👑⚒ crest · CHRONICLE
  SEALED · 99/99 · grail-wall buttons — and the 99 restore rows fold behind ONE 📜 disclosure.
- Gates: 64 specs green incl the full forge lifecycle set · 20/20 blocks parse · before/after
  screenshots archived.

### 🌙 N5 · v778-pre — THE BUTTON MATRIX, no loopholes (Konyo live, both directions) ✅
- **BUG A — the zombie stare**: our own dead child agent is a ZOMBIE until reaped; os.kill(pid,0)
  succeeds on zombies, so the stop thread waited the full 90s farewell window on a corpse (the
  stuck-'stopping' + disabled-ON cascade). _pid_alive now poll()s our child (answers truthfully
  AND reaps). Every transition: sub-second.
- **BUG B — the phantom window at ON**: Grok's v773 restructure held DUPLICATE /api/on handlers —
  the live one still spawned the board window (my v777.1 had fixed the dead copy). ON and RESTART
  spawn NOTHING now; grep _open_board_once call sites = /api/board only.
- **SIM = THE LAST SESSION** (Konyo: "simulation mode should be recent last session"): the button
  is THE THEATRE again, auto-playing the newest real session — the v765 semantic restored over
  Grok's canned-feed revert; `tvd sim` keeps the canned feed for devs.
- API truth matrix after fixes: ON→live ✓ · STOP→off 0.6s ✓ · OFF→off 0.6s ✓ · RESTART→live ✓ ·
  SIM→sim/off ✓ · windows spawned: ZERO across the whole run.

### 🌙 N6 · v778 — WAVE D: the family locked (build waves COMPLETE) ✅
- Dock-clearance via scroll-margin on every family card (live-measured --dock-h+24) · Funi/Fsets
  LOWs re-verified resolved · the 1-1 stop sync board half CONFIRMED in (st.stopping → instant
  OFF AIR on the site).
- **THE FAMILY LOCK SPEC** (tests/v775_tab_family.spec.ts, 9 red-tripwires): per-tab spine +
  GOLD accent + no-overflow at three widths · unclipped subs · the ⌂ CONSOLE pill contract
  (?app=1 only).
- NIGHT BUILD ARC COMPLETE: v774 host+rail → v775 spine → v776 Tools chrome → v777 sealed Forge
  → v778 locks. Plus the live-run battle round: v776.1/777.1/777.2/778-pre (SIM toggle, window-pin
  auto, ON spawns nothing, zombie stare, SIM=last-session theatre).
- Gate: 29/29 (family 9 + board 15 + console 5) + prior wave suites green.


### 🎯 v779 — THE HONEST EYE (Grok picks up Fable's capture-pin mystery) ✅
- **Root cause 1 — THE STALE-FILE LIE**: window capture trusted a pre-existing `live.bmp` when
  `screencapture` wrote nothing (rc=1, size=0). Agent claimed pin; film was last night's desktop.
  Fix: capture → unique temp → `os.replace` only on real bytes. 3 unit locks.
- **Root cause 2 — TCC**: Python-as-responsible (control→agent) needs its own Screen Recording
  grant; Terminal's checkbox does not cover it. Boot preflight + `CGRequestScreenCaptureAccess`
  + Settings deep-link; Mac spawn drops `start_new_session` (setsid broke the chain).
- **Live film**: `/frame` prefers `eye.jpg` (refreshed each capture) over frozen `read.jpg`.
- **ONE version truth**: agent/control/UI/`D2R_BUILD` → **v779**.
- Live-verified: pin `D2R.exe · Diablo II: Resurrected`, film = Rogue Encampment, read #1 lands.
- Gates: agent+control **83/83**.


### 🎯 v779–v783 — GROK SHIP ARC (Konyo: finish Claude stuck path · one window · live film) ✅

**Entry:** Fable handoff `HANDOFF_TO_GROK_capture_pin_2026-07-18.md` — window pin claimed D2R,
film showed desktop; version drift v774 stamps vs tip v778+.

#### Root causes closed
1. **STALE-FILE LIE (v779)** — `screencapture` fail left old `live.bmp`; exists+size trust gate
   claimed pin success. Fix: temp → promote only. Screen Recording preflight + Mac no-setsid.
2. **Chrome/CrossOver pin steal (v779.1)** — bible tab title "D2R" / CrossOver Home out-scored
   game. Fix: browser blocklist + bare CrossOver launcher ban + D2R.exe absolute score.
3. **ON flapping (ops)** — 3 control apps fought one port. Clean single process.
4. **Second window (v781)** — Open Board → `/api/board` spawned `--board-window`; dual Desktop
   launch opened another pywebview. Fix: same-window nav; port-in-use refuses second window.
5. **Film freeze on READING (v782)** — `claude_read` blocked capture loop. Fix: vision worker
   thread + snap.bmp; capture continues.
6. **Film lag (v783)** — dedicated ~5fps JPEG film thread, pick TTL cache, UI poll 300ms,
   priority gap 1.2s / cruise 4s. Measured ~2fps eye updates live.

#### Product wires locked
| Surface | Truth |
|---------|--------|
| Capture | AUTO pin `D2R.exe · Diablo II: Resurrected` |
| Film | `eye.jpg` via film thread → `/frame` |
| Session | `sessionId` per ON → theatre pages |
| SIM | In-console theatre = newest journaled session |
| Board rail / TV·D | Same window `/board?app=1#tab` |
| Journal | `sessions.jsonl` + `hist/{frameId}.jpg` cross-ref |
| Stamps | agent · control · UI · D2R_BUILD = **v783** |

#### Gates (this ship)
- `tv.test_agent` + `tv.test_control` → **87/87 OK**
- Live button matrix (v781): ON/OFF/RESTART/STOP/BOARD-nav · **0 board-window spawns** · 1 control
- Live: mode live · bridge · pin D2R · film updating · sessionId minting

#### Honest limits (do not lie to Konyo)
- Console **film** tracks game (~0.5s class).
- **OCR** provisional names ~50–150ms when text is still + readable.
- **Claude deep** still multi-second (subscription vision) — stop on piles, don't expect 60fps ID.

#### Commits (main, ship stack)
- `6f55cee` v779 Honest Eye (stale-file + TCC)
- `2e6e5cd` v780 Session Film Truth (sessionId + theatre stamps)
- `7be215b` v781 One Window Console
- `c6509df` v782 Live Eye Never Freezes
- `7d6dcbc` v783 Snappy Film

#### Operator notes
- One TV DIABLO window only (Desktop re-launch refuses second).
- SIM = last session reel in-console (not canned agent; `tvd sim` still for dev).
- Pop-out board only via `/api/board?popout=1` (UI never calls it).
- Grant **Python** Screen Recording if capture dies after app relaunch.

🏓 **PING → Konyo:** stack is online at v783, suites green, ready for a real pile-hover farm run.


### 🎯 v784.W — Windows twin parity (cousin app) ✅
- `capture_win.ps1` → **v784**: default `TV_CAPTURE=auto` (pin native D2R.exe), browser/editor
  blocklist, absolute D2R scoring, temp→promote live.bmp, writes **eye.jpg** for console film,
  `cap_target.json` for status row, ~200ms poll.
- Agent `--watch`: prefers live.bmp for settle; reads cap_target into `_CAP_TARGET` (🎯 pin events).
- control `_env_clean`: sets `TV_CAPTURE=auto` on Windows when unset.
- Launchers/install/README stamped for one-window + SIM exact reel product (same as Mac).

## 🌙 Night round 2 → v785 "The Vigilant Film" (Fable, 2026-07-18 ~02:30)
Round-2 critique (Fable third-eye, banked during Grok's v779–v784 arc) → implemented:
- **Film honesty governor** (the round-2 sleeper): agent surfaces `eyeAgeMs` on /state, control passes it,
  stage DROPS `film-on` when the eye is >4s stale — the film never claims LIVE on a dead frame.
  Eye.jpg lifecycle: `_eye_clear()` on farewell + control-side belt in stop_agent (force-kill path).
- **SIM glow truth**: `.lit` now follows `TH.open` (paint + thLit); Grok's `.on` toggle was styleless
  on `.act` buttons — the primary SIM card finally glows on its own click path (button-truth doctrine).
- **Eye fidelity 1280/q65** (was 720/q55): the stage star is no longer the softest image in the pipeline;
  still ~100ms sips on localhost, Theatre stays 2560 archival.
- Dropped round-2 pick #2 (tabs → singleton board): overruled by Konyo's explicit one-window decision (v781).
- 3 new unit locks (eye age fresh/stale/none · clear idempotent). Suites 77/77 + 16/16.

## 🌙 Night round 3 → v786 "The Open Doors" (Fable, ~03:30)
R3 pick 1 (CRITICAL): 4 of 5 app-rail tabs were dead doors — v680 bare-hash normalizer clobbered
#session/#forge/#funi/#fsets → #tools before the router ran; family tripwire drove switchTab()
directly so it stayed green. Fix: ?app=1 = INTENT, normalizer exempts app context; new
v786_deeplinks.spec.ts walks the REAL consumer path (6/6). Plus two Konyo live fires:
- SIM story pacing: real 6-30s read gaps pinned the 4s cap → crawl. Now story-time (raw/8,
  clamp 500-2200ms); reel pick needs SUBSTANCE (reads>=3 + named first) — restart shards
  no longer win "newest"; matrix runs send test:true → TV_NO_JOURNAL (no more shard pollution).
- Windows cousin 'ON AIR just spins': claude-CLI preflight + dead-at-boot detection return
  ok:false with the REASON + fix command; UI toasts it loudly. No more silent spinner.
Deferred to next ships: R3 pick 2 (installer copy/plist v761 drift), pick 3 (vault double-register),
sleeper (replay sim-flag). Suites 77+16 OK, matrix stamped v786.

## 🌙 Night → v787 "Honest Replay" (Fable, ~03:50)
R3 picks 2+sleeper: replay/harness reads now stamp sim:true (agent emit → rec field — the flag
initially died at the rec-builder allowlist, the EXACT boundary class R3 warned about; caught by
the new round-trip lock before ship). Board vault-commit path returns early on rd.sim: replay is
view-only, NEVER re-vaults history. Installer truth: plist 761→787, last-line copy is app-truth
('press ON AIR' — 'flip the switch' extinct repo-wide). 2 new locks (sim flag travels · live reads
clean). Suites 79/79 + 16/16.

## 🏓 Grok R4 (SuperGrok CLI back!) → v788 "No Cliff" (~04:05)
Grok's console-perfection round, grounded in real code (he read SESSION_CAP): TOP 5 = fault lamp/
scoreboard · kill the 240-read cliff · theatre highlight-cut · endurance paint · Windows twin lane.
v788 ships #4 first (product-ending): the sleep(60)-forever halt at 240 reads is dead — soft cruise
throttle (+6s→+30s gap creep), eye NEVER stops, scoreboard will show density. Lock: publish past cap.
80/80 + 16/16. Grok's remaining picks queued as v789+.

## 🏓 Grok R4 #1 → v789 "The Fault Lamp" (~04:20)
Agent _health() on /state (eyeAgeMs · visionBusyMs since _VISION_BUSY_AT · lastReadAgeMs ·
sessionMs · named/vaulted tallies) → control passthrough → stage FAULT BANNER (NO EYE >6s ·
VISION SLOW >45s · STALLED >3min) + LIVE bug greys while faulted + 👁 Vision / ⏱ Last-read
signal rows. Quiet death is forbidden. NOTE: first patch died on an ambiguous anchor
(_VISION_BUSY ×2) — partial-apply caught by suite, re-anchored. 82/82 + 16/16.

## 🏓 Grok R4 #2 → v790 "The Highlight Cut" (~04:35)
Theatre = broadcast reel, not slideshow: default 🎬 CUT keeps loot-chain/discovery/named/area-change/
farewell/bookend beats with content-weighted dwell (vault 2.2s · discovery 1.8s · named 1.4s ·
empty 550ms); 📼 FULL one click, position preserved across toggle; gold chapter ticks on area change;
raw epoch demoted to film tooltip. 82/82 + 16/16.

## 🏓 Grok R4 #3 → v791 "Endurance" (~04:50)
2-hour ON without thrash: adaptive self-scheduling poll (300ms only while data-state=on AND eye
fresh <2.5s; else 1.5s), film cache-bust skipped when the eye is still (>2.5s), endurance mode
after 10min continuous ON freezes decorative keyframes (LIVE bug + film + fault banner stay
animated), prefers-reduced-motion = instant endurance. 82/82 + 16/16.

## 🌙 R3 pick 3 → v792 "One Name" (~05:05)
Vault + chronicle share ONE canonical identity: tvVaultRegister resolves suffix-tolerant ITEMS
match + canonical set-piece name (same as tvChronicleRoute) so 'Harlequin Crest' vs
'(Shako)'-suffixed are never two tiles; belt-loop fills gaps only (_regd set from routes-loop) —
'Ist' + 'Ist Rune' dual registration dead. Board specs 21/21 + suites 82/82 + 16/16.

## 🏓 Grok R4 #5a → v793 "Capture Lamp" (~05:15)
Windows capture_win.ps1 death is now first-class: _capture_health() → LINKED/DEAD/RESTARTED on
/api/status, auto-restart ONCE with loud log, UI fault 'NO CAPTURE' outranks NO EYE. (OCR twin
lane = queued for cousin-night, needs a Windows box to verify.) 82/82 + 16/16.

## 🏓 Grok R5 #4 → v794 "No Poison" (~05:35)
Learn-dead gate: ONLY explicit vision-confirmed scene=transition (mode empty/error/timeout NEVER
learns — one chatty-CLI hiccup on a real inventory freeze used to blind that panel class for the
night + across restarts via known_frames.json). _parse_read: right-to-left balanced-object scan
with known-key check survives worker chatter/truncation. Old test asserting the poison behavior
RECALIBRATED. 85/85 + 16/16.

## 🏓 Grok R5 #2 → v795 "OCR Rescue" (~05:50)
OCR-won / Claude-lost frames no longer vanish: empty deep + OCR names → seed floor-SEEN into
LootLifecycle (never vault from seed) + ocr_seeded on the rec + ONE re-fire ticket (_REFIRE_SIG)
so the same-view burn allows a second read of that freeze. 87/87 + 16/16.

## 🏓 Grok R5 #3 → v796 "The Multiset" (~06:05)
Second drop of the same name COUNTS: instance-aware vaulted ledger (count/ts), commit consumes
provenance (seen popped too — the echo-revault bug caught by the new lock), fresh sighting
re-vaults via floor-again doctrine or multiset branch; _norm_name strips Superior/Ethereal
prefixes so floor↔panel names share one chain key. 89/89 + 16/16.

## 🌙 Konyo order (theatre = video + forensics) → v797 "Frame Forensics" (~06:20)
Beat payload now carries the FULL read truth (ocr_names/confirmed/ocr_seeded/conf/lifecycle_tags/
sim/model/completedTs) + theatre caption grows a forensics strip: T+mm:ss.mmm session clock ·
⚡OCR lane vs 🧠 deep lane names · latency ms · ✓confirmed count · 🛟 ocr-rescued · conf · 🕐 answer
delay · per-name lifecycle tag chips. 89/89 + 17/17.

## 🏓 Grok R6 V1 → v798 "The Playhead" (~06:45)
The slideshow is dead: piecewise-linear theatre axis P[] (content-weighted holds 320-2400ms,
quiet-gap collapse 60-180ms, same-area 8s+ quiet → 80ms sliver), rAF playhead p advances at
speed×real-ms (2×/4× = dp/dt only, never rebuilds the axis), binary-search beat binding,
T+mm:ss.mmm + wall dual clock in the header, timeline widths ∝ theatre time (equal dots lie),
OCR+deep same-frame rows MERGE into one two-lane beat (no more discard). Axis sanity-tested in
node: vault holds 2s, 38s quiet → 0.6s. 89/89 + 17/17.

## 🏓 Grok R6 V3 → v799 "The Film Engine" (~07:05)
WebView traps closed: decode-before-swap (probe Image warms the decoder, film.src flips only
when ready — no white flash at 4×), bounded 3-slot preload pool (±2 neighbors, never a decoded-
bitmap pileup), /hist Cache-Control immutable, ?w=1280 disk-cached theatre derivative (sips,
cache1280/) — full 2560 original = click the film. 89/89 + 17/17.

## 🏃 MARATHON II opens → v800 "The Read Card" (~07:40)
Grok R6 V2 drawer: ℹ / `I` toggles a monospace right-drawer with the COMPLETE beat truth —
identity (read#/frame/session/lane/model/sim) · clocks (capture ms, answer delay, vision+ocr
latency, conf) · nine name-set columns · lifecycle chain per name · context (note/stash/intent/
farewell). Follows the playhead live. Keyboard transport: ←/→ beat snap · space play/pause.
89/89 + 17/17.

## 🏃 v801 "The Feel Pack" (~07:55) — Konyo: 'CONSOLE + SIMULATIONS, perfected'
Drag-scrub (pointer capture, playhead follows the sweep live, auto-pause), 110ms aperture cut
on beat change (opacity+scale, never a blurry dissolve), vault beats glow mint ON the film,
cast chips stagger in 30ms apart ('read aloud' feel). 89/89 + 17/17.

## 🏃 v802 "Scrub Thumbs" (~08:05)
Hover the timeline → floating 160px thumbnail of that exact frame (+read#/area caption), like a
real video player scrubber. Server derivative whitelist widened to 160 (cache160/). 89/89 + 17/17.

## 🏃 Grok R7 wow #1 → v803 "Instant Replay" (~08:20)
⏪ appears on any vault beat (film + strip, R key): binary-seek 8s of wall time back, play 0.5×,
freeze 1.2s on the find with a mint lower-third 'NEW FIND · <names>', then restore speed.
Sports-broadcast dopamine, zero new capture — pure P[] reuse. 89/89 + 17/17.

## 🏃 Grok R7 wow #2 → v804 "Loot of the Night" (~08:35)
Reel end = credits roll: 🏆 slate over the film with session stats (duration/reads/named) +
every vault ranked with count and T+ timestamp; 8s auto-hide, SPACE/click closes, resets per
session load. Empty-vault run gets 'the grind continues'. 89/89 + 17/17.

## 🏃 ARMY MERGE 1/3 → v805 "The Durable Night" (journal-agent, ~08:50)
fsync on every journal append (crash mid-write can't erase the night); 4MB cap now ROTATES
(sessions.jsonl → sessions.1.jsonl via os.replace, prior rotation overwritten) instead of the
racy half-truncate rewrite; replay.load_journal() concatenates rotated+live chronologically;
torn-line tolerance locked. .gitignore: tv/sessions.*.jsonl. Fable gate: patch anchors 1-match,
92/92 + 17/17.

## 🏃 v806 "Full Deck" (~09:00)
0.5× slow-mo joins the speed cycle (0.5→1→2→4), Home/End = reel bookends, J/K = ±5 beat jumps.
The transport deck is complete (Grok R7 #4 spec). 92/92 + 17/17.

## 🏃 ARMY MERGE 2/3 → v807 "One Engine" (site-parity-agent, ~09:15)
The website theatre runs the SAME v798 playhead as the app (thz- port, 9 anchors, drift-abort
guard): piecewise axis, rAF playhead, dual T+/wall clock in the topline, proportional dots,
press-at-end rewind, click-seek moves the playhead. Dual-engine drift is dead. New guard spec
v807_site_playhead (fails on unpatched — verified genuine). Fable gate: 7 specs + 24 board/family
+ 92/92 + 17/17 all green.

## 🏃 ARMY MERGE 3/3 → v808 "The Doctor" (doctor-agent, ~09:30)
GET /api/doctor: 10 checks (claude_cli via _env_clean PATH · probe-stub (never spawns CLI) ·
agent/control ports · python Store-stub detection · WebView2 registry · capture lamp · live-frame
freshness (blocks only when LIVE) · bridge · stale pids), ok = no block-failures, agent-OFF never
fails it, ver mirrors status stamp at runtime (drift-proof). UI: boot failure → doctor runs →
every blocker in the toast as 'id: detail → fix'. Fable gate: 24/24 control (7 new locks) + 92/92.

## 🏃 Grok R7 wow #3 → v809 "The Night Card" (~09:45)
📼 in the theatre strip: GET /api/export?n= writes Desktop/TVDIABLO_<sid>.json (full beats) +
.md story recap (T+ stamps · area · 🏦/💬🏆/🗑 seals · farewell). LIVE-VERIFIED on Konyo's real
session 1 (10 beats, Chaos Sanctuary, Annihilus in the stash reads). Marathon II = v800-v809,
10 versions: Read Card · Feel Pack · Scrub Thumbs · Instant Replay · Loot of the Night ·
Durable Night · Full Deck · One Engine · The Doctor · Night Card. 92/92 + 24/24.

## 🏃 MARATHON III opens → v810 "The Chain Story" (~10:00)
Hover any cast chip in the theatre caption → floating popover with the item's chain for that beat
(ocr › floor › hold › vaulted 🏦 / thrown 🗑 / discovered 💬🏆) + short-label tag (owned/skip/
no-chain map). Delegated hover, fixed-position, pointer-safe. 92/92 + 24/24.

## 🏃 Grok R8 sleeper → v811 "The Generation Ring" (~10:15)
The R8 sleeper was real: second rotation OVERWROTE sessions.1.jsonl (months of nights, zero lamp).
Now: ring shift .4→.5 … .1→.2, live→.1 (~20MB ≈ months), cap event on rotate, replay concats
.5→.1→live oldest-first, doctor journal_gens check. Lock: GEN1 survives a second rotation.
93/93 + 24/24.

## 🏃 v812 "Whole Truth Export" (~10:25)
R8's sibling claim-gap closed: /api/export json now includes sess.raw = the RAW journal rows
(sessionId-filtered across the generation ring, ts-range fallback) with every field the theatre
projection drops; .md story seals ⏳ holds. LIVE-VERIFIED: 10 raw rows with anchor/
gone_candidates/farmed_names on session 1. 24/24 + 93/93.

## 🏃 v813 "One Budget" (~10:35)
cache1280/cache160 derivatives are counted in the HIST_MB ceiling, pruned as twins of their
source, and orphans (source already pruned) are swept. Lock: derivative-survives-source +
orphan-sweep. 94/94 + 24/24.

## 🏃 v814 "The Chapter Slate" (~10:45)
Highlight-cut area jumps flash a 620ms scanline slate (🗺 new area, Cinzel gold over CRT lines) —
the cut admits it skipped. 94/94 + 24/24.

## 🏃 v815 "Replay Integrity" (~10:55)
Doctor session_integrity check: % of journal-tail reads whose hist frame EXISTS + sessionId
coverage (live probe: frames 100% of 200 · sid 38/200 — pre-v780 rows unstamped, expected).
24/24 + 94/94.

## 🏃 v816 "Triple Lamp" (~11:05)
Status carries bibleVer (30s-cached regex of D2R_BUILD); footer reads 'v816 control · board v816'
and turns AMBER on drift; TestTripleParity locks bible==agent (test_stamps_match already locks
agent==control) — the three stamps can never silently fork again. 25/25 + 94/94.

## 🏃 v817 "Update Truth" (~11:20)
GET /api/update: git fetch + rev-list count behind origin + latest ship subject; footer is now
clickable → toast '✓ up to date' or '⟳ N behind — latest: … · git pull, then relaunch'.
94/94 + 25/25.

## 🏃 v818 "The Twin Lane" (~11:40) — DARK SHIP
Windows OCR fast lane: tv/ocr_win.ps1 (Windows.Media.Ocr, inbox, WinRT await helper) speaks the
EXACT ocr_mac worker protocol (stdin path → stdout {"ms","lines","confs","mode"} JSON line);
agent _ocr_worker_cmd() dispatches per platform (TV_OCR_BIN override > win ps1 > mac bin), every
failure emits mode:err so the fast lane degrades to vision-only, never dies. No per-line
confidence in the Windows API — flat 0.8 documented. NEEDS COUSIN-BOX LIVE VERIFY.
Locks: mac/win/env-override dispatch. 97/97 + 25/25.

## 🏁 v819 "Marathon Close" (~11:55)
MARATHON II (v800-809) + III (v810-819) COMPLETE. Closer ships: COUSIN_CHECKLIST.md (10-step E2E
with truth surfaces at every step) + BUGS.md REG-021/022/023 (capture lie · launcher outrank ·
rotation erasure). Remaining for next arc: cousin-box live verify (twin lane + checklist run) ·
cousin state isolation (R8 #10, invasive) · site READ-CARD/forensics parity ride-along.
97/97 + 25/25.

## 🎬 v820 "The Curtain Falls" (~12:10) — Konyo live: 'simulation is a black screen'
REG-024: hidden attribute loses to author display: — credits+slate overlays blacked the film
while hidden=true. Fix: [hidden]{display:none!important} for all five theatre overlays (rule
asserted in gate). Same debug also fixed: /hist ?w= derivative (router stripped the query —
now 1280px/244KB actually serves, was 2560/1MB) + T+ clock lights at open. VISUAL VERIFY:
headless screenshot shows the full Chaos frame + forensics + timeline. 97/97 + 25/25.

## 🎬 v821 "The AI Read Line" (~12:25) — Konyo: 'WHERE is the AI read at the time of'
The model's answer is now the HEADLINE of every beat, dual-stamped: 📸 CAPTURE wall-clock.ms +
T+ session clock + frameId › 🧠 AI READ wall-clock.ms (+Ns after the frame) + model/latency/conf
› 📖 IT SAW <verbatim names in mint> (or 'honest empty') › ⚡ OCR lane when present › SIM badge.
READ CARD drawer opens BY DEFAULT with the theatre (I closes). VISUAL-VERIFIED: screenshot shows
CAPTURE 2:51:18.128 → AI READ 2:51:25.036 (+6.9s) on the Chaos frame. 97/97 + 25/25.

## 🏃 MARATHON IV opens → v822 "Site Read Line" (~12:45)
Website theatre parity with v821: hist entries now carry completedTs/names/ocr_names/ocr_seeded/
sim (producer) + thzAiRead block in the caption (consumer) — 📸 CAPTURE vs 🧠 AI READ vs 📖 IT SAW
on the site reel, old rows degrade gracefully. 16 board specs + 97/97 + 25/25.

## 🏃 Grok R9 sleeper #8 → v823 "Fast Lane Clock" (~13:00)
ocr_ms now projected on theatre beats (claim/consumer 8-for-8: journal had it, theatre dropped
it); lane-merge keeps the fast clock unconditionally; ⚡ OCR row reads '31ms (instant, at the
frame)' vs 🧠 seconds later — the dual-lane timing story is complete. Forensic-fields lock
extended. 25/25 + 97/97.

## 🏃 Grok R9a → v824 "Broadcast Hierarchy" (~13:20)
One read card: old accuracy strip shrunk to read#+lock+story flags (clocks live in the read line
only); cast chips render ONLY with seals (IT SAW is the one cast row); T+ deduped to the topline;
rows wrap; IT SAW hero-sized; drawer default-CLOSED, auto-opens on the FIRST story beat
(names/vault/discovery/farewell), `I` preference persists in localStorage; film SHARES the stage
with the open drawer (right offset, 200ms ease) instead of being painted over. VISUAL-VERIFIED:
full Chaos frame + clean card + ⚡ OCR 249ms line. 97/97 + 25/25.

## 🎬 v825 "Cinema Mode" (Konyo live ×2, ~16:10)
Drawer trap fixed (it covered its own ℹ toggle): drawer stops above the transport strip + sticky
✕ close + I preference. ⛶ FULLSCREEN cinema: theatre fills the entire window (F toggles, Esc
exits, true requestFullscreen attempted, auto-exits with theatre close). UX-verified headless:
open→✕→closed, cinema 1120×800 full-window, Esc off. 97/97 + 25/25.

## 📹 v826 "The Footage" (Konyo: 'every frame per second', ~16:30)
The reel is now LITERAL video: agent film loop archives the eye at 1fps (f_<ms>.jpg, own 3600-
frame cap inside the shared MB ceiling, twins pruned); /api/session interleaves footage frames
into the session window as film-only beats; 📼 FULL plays them at REAL time (gap-clamped 120-
1500ms → 1s/frame at 1×, 2×/4× speed it) with the STANDING AI read + '📹 footage · hh:mm:ss.ms ·
the eye, 1 frame/sec' annotation; 🎬 CUT still tells the story (footage dropped); hairline
timeline ticks. Next sessions recorded from v826 onward carry footage. 97/97 + 25/25.

## 🏃 ARMY MERGE → v827 "No Freeze Left Behind" (settle-agent, ~16:50)
The last big loot-truth hole is closed (Grok R5 #1 / R9 #2): distinct freezes landing during a
7-90s vision call are COPIED to frames/queue (ring cap 4, sig-deduped, 120s stale-drop, reading-
view excluded) and the NEWEST drains through the identical dual-lane pipeline the instant the
read frees (drain re-arms _VISION_BUSY — a second concurrent call is impossible); inline dispatch
lifted into _launch_vision shared by both paths; queue dies with the session. 6 new locks.
Fable gate: 103/103 + 25/25.

## 🎯 v830 "Location Truth" (Konyo timestamp forensics, ~17:30)
His two frame-exact reports fixed at the root: (1) Flame Rift GC hovered in INVENTORY while
stash open → was scene-stamped 'stash'; (2) EQUIPPED Shako ('Shift+Left Click to Unequip')
treated as farm loot. Now: prompt asks names_loc per name (equipped/inventory/stash/floor,
with the panel-side + unequip tells), parse round-trips it (allowlisted), LootLifecycle:
equipped = tag-only (never vault/hold), inventory-side during stash = HOLD flow, only true
stash-panel names commit; board: equipped_names → quiet idempotent tvChronicleRoute (the
'tallies on the way' he asked for), NEVER vault; IT SAW badges 🎽🎒🏦🧱 per name. 5 locks
encode his scenarios verbatim. Neither original case falsely vaulted (stash-no-chain gate
held) — this fixes classification + future truth. 108/108 + 25/25.

Also this stretch: v829 Pinpoint Seek (stale-probe race — arrows always land the right frame;
honest run-span '· ran 3m41s · 10 AI reads' in the header).

## ⏱ v831 "Real Time" (Konyo live: 'stuck going right' + 'timeframe span based', ~17:55)
(1) The stuck reel: ▶ at the end silently re-paused on the last frame (and → was dead there).
Now ▶-at-end REWINDS and plays (verified: End → play → read #1 → rolling to #4), ArrowRight at
the last beat toasts 'end of the reel'. (2) ⏱ REAL mode joins the cycle (🎬 CUT → 📼 FULL →
⏱ REAL): theatre-ms == wall-ms, the reel runs EXACTLY the session's true duration at 1×
(2×/4× compress) — with v826 footage sessions this is literal video playback. 108/108 + 25/25.

## 🧠 SIMULATION ARC opens → v832 "Journal the Brain" (+order fix, ~18:40)
SIMULATION_SPEC.md committed (Konyo's north star: SIM = visual debugger of the AI's mind, ~50
versions, ON AIR frozen; Grok appended a full addendum DIRECTLY into the spec — dispatch
decomposition, parse audit, pre-triage designs). v832: every read journals raw model words
(2KB, ring-stripped/journal-kept), dispatch ctx {motion·settleTicks·interest·priority·origin
live/settle-queue/farewell}, promptVer p830; drawer grows THE DISPATCH + THE THOUGHT sections
('not recorded before v832' for old rows — never fake). v832.1: Konyo's scramble report —
pre-v784 rows stored COMPLETION time as ts; 10-22s latencies interleaved captures → film jumped
non-logically. Beats now sort by the PHOTO's own clock (frameId suffix ms) with ts pinned to it.
108/108 + 25/25.

## 🏓 R11 (Grok addendum A2.1) → v833 "Dispatch Anatomy" (~19:00)
ap_interest exposes its decomposition (parts= out-param; parts sum == score, lock added);
dispatch ctx grows peak/gapMs/emptyStreak/apMode/queueDepth/interestParts; drawer DISPATCH
section renders '= parts peak +0.45 · priority +0.25 …'. 110/110 + 25/25.

## 🏓 R12 → v834 "The Eraser" (Konyo: 'option to delete a session', ~19:15)
POST /api/session/delete {n}: removes that session's journal rows across the generation ring
(atomic tmp+replace per file), its read frames by frameId, footage in its window, derivative
twins — other reels untouched. 🗑 in the strip with two-click arm (3.5s, no native dialogs),
reloads the picker after. 110/110 + 26/26.

## 🏓 R13 (Grok A2.2) → v835 "Said vs Survived" (~19:35)
Parse audit through _parse_read: strategy (first-last/balanced), rawLen, normalized[] (scene
clamps with from→to→why), dropped[] (invalid locs, name truncation) — journaled per read,
drawer section renders ⚠/✂ lines or 'clean — everything the model said survived'. 3 locks.
113/113 + 26/26.

## 🏓 R14 → v836 "The Decision Chain" (~19:55)
_reason_for(tag, loc): every verdict speaks WHY in Konyo's language ('read in the stash but
NEVER seen on floor/inventory this session — no provenance, blocked'); rec.decisions =
{name: {loc, tag, why}}; drawer chain section: name 🎽/🎒/🏦/🧱 › tag › why. 115/115 + 26/26.

## 🏓 R15 → v837 "The Session Shelf" (~20:10)
📚/S opens the shelf: every recorded run as a card (session#, date+time, span, reads, named,
areas; current reel ringed mint) — click to load, click-away to close. Verified live: 26 cards.
115/115 + 26/26.

## 🏓 R16 (Grok VERIFY) → v838 "Honest Anatomy" (~20:30)
Grok read the v833-v837 diffs and caught a forensic POISON: the dispatch ctx was journaled AFTER
the loop reset its inputs — peak always 0.0, priority always False, gapMs ~0, apMode always
'read' on every live row (the anatomy shipped to fix forensics was itself lying). v838: pre-reset
snapshots (used_peak/used_priority/_d_gap/_d_apmode) + namedStreak/frameSrc; queue-drain ctx now
honest ('queued freeze — live motion fields n/a' + heldMs); _reason_for holding case; conf-clip +
NaN audit rows; agentVer + promptHash identity (A2.9, bisectable eyes). Remaining A2 gaps (pre-
triage, chain, board-write, vision, ocr_raw, skip events, decision river chrome) = the arc's
next ships, logged. 115/115 + 26/26.

## 🛡 v839 "Archive Shield" (Konyo: 'history all black' — REG-025, ~20:50)
Footage's MB pressure DELETED the old sessions' read frames (2599 f_ vs 11 surviving reads,
482MB). v839: footage gets FOOT_MB=900 sub-ceiling and evicts FIRST; reads pruned only by their
own budgets; HIST_MB default 1500; pruned beats say '⚠ photo pruned from disk' honestly; film
element clears stale url after frameless beats. Lost photos unrecoverable — journals intact.
115/115 + 26/26.


### 🎯 v840 — JOURNAL SHIELD + ON AIR / SIM forensics (Konyo: long run bugs) ✅
**Version truth:** tip **v840** (was already v839 Archive Shield before this ship).

#### Live forensic (this machine, agent OFF)
- Journal recent: **173 rows / 19 sessions**; integrity **~6% frames present** on tail
  (274 missing hist files overall) — SIM reels hollow for most of the night.
- Hist composition before prune: **13 AI-read jpgs + 2600 footage f_*.jpg (475MB)**.
- Log: thousands of `screencapture failed` lines (Screen Recording / no D2R at end of run).
- Capture probe now: Screen Recording preflight OK; D2R window not open → full screen.

#### Root causes
1. **Footage drowned the archive** — 1fps film filled disk; older AI-read frames pruned
   despite REG-025 intent. SIM cannot show photos that no longer exist.
2. **Capture-fail log flood** — every poll printed the same TCC warning (masked real events).
3. **tmp ghosts** — many `live.bmp.tmp.*` left from interrupted captures.

#### Fixes shipped (v840)
- **Journal shield**: hist prune never deletes a read frame still referenced by sessions.jsonl
  (+ generation ring scan).
- Footage ceiling cut: FOOT_MB 400, FOOT_KEEP ~30min (1800); HIST_KEEP 800.
- Capture-fail **throttled to 30s** + boot cleans `*.tmp.*` / `.part` files.
- SIM session list: `frameWant` / `frameMissing` / `archiveOk` honesty.
- Doctor session_integrity reports missing count (warn).
- One-shot prune: footage **2600 → 1800**.

#### Gates
- `tv.test_agent` + `tv.test_control` → **142/142 OK**

#### Honest limits for Fable / Konyo
- **Past** sessions with missing hist stay partially blank (cannot invent photos).
- **New** ON AIR runs keep every journaled AI frame.
- SIM is the mind debugger (SIMULATION_SPEC); ON AIR frozen-quality work continues via
  journal-shield + quieter capture + doctor.

🏓 **PING → Fable / Konyo:** v840 shipped forensically; re-ON with D2R open + Screen Recording
on Python; use SIM shelf — prefer reels with archiveOk / high frames count.


### 🎯 v841 — SCOUT LANE (Konyo: cut stop+hover out of the product) ✅
**Idea:** secondary snapshot + continuous light OCR so loot TEXT mid-play triggers dual-lane
without a multi-tick full settle / deliberate freeze.

**Hard limit (honest):** D2R icons alone still have no names on screen — we never invent from
icons (read-only doctrine). Scout needs *some* on-screen text: ground loot labels, brief
tooltips, open panels. Play tip: enable show-items / loot name labels for max coverage while
walking.

**Code:**
- Every ~0.45s (while motion ≤ 0.20 blur gate): copy frame → `frames/scout/hit.bmp` → OCR.
- Fresh item-ish names → archive + dual-lane with `dispatch.origin=scout` (no settle wait).
- While Claude is busy: scout hits **enqueue** a freeze for settle-queue drain (secondary bridge).
- Dedupe ~40s per normalized name so one tooltip does not thrash.
- Env: `TV_SCOUT_S`, `TV_SCOUT_MOTION`, `TV_SCOUT_GAP`.

**Gates:** 143/143 agent+control.
