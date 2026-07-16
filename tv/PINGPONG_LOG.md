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
