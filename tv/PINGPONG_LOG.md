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
