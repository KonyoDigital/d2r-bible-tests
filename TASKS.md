# THE TASK LIST — D2R Farming Bible

**This file exists because the list did not survive a restart on 2026-09-01.** It lived only in a
session's own task state. The memory queue recorded the NUMBERS (`#135 · #143 · #159 …`) and not
what they were, so after the restart there were twenty-two numbers and nothing behind them.
Recovered from the 688 MB transcript. **It is a tracked file now. A list that lives in a session is
not a list.**

Numbers are the session's own task ids, **not GitHub issue numbers** — GitHub `#135` is a different,
closed thing. Where a task has a GitHub issue, it is named explicitly as `gh #NNN`.

Status: `READY` may be applied now · `BLOCKED` names what blocks it · `HIS CALL` waits on Konyo ·
`SHIPPED` carries the version.

---

# ✅ LANDED 2026-09-02 — four ships, and what each one CLOSED

> Written because this file went four versions stale (last touched at v2435) while the work carried
> on somewhere else. A task file that stops moving is a task file nobody can restart from, which is
> the exact failure its own header is about. Live view, regenerated from here:
> **claude.ai/code/artifact/6291b84e-b408-4f04-8a38-ec48826bc753**
>
> ⚠ **2026-09-03 — the board changed shape, and the reason matters.** Every row lived in ONE
> document (`board/state`), which has now grown past the size cap the agent reads through: it comes
> back ELIDED, so the rows could no longer be diffed, and because `sections` is a single field any
> write would have replaced all of them blind. That is precisely how a pending row gets pruned by
> accident. Rows are therefore mirrored one-per-document into `rows/`, which can be read and
> updated individually. `board/state` is never deleted — it stays the frozen pre-migration source.
> The mirror runs once, under a lease, and writes its completion flag LAST, because a mirror
> interrupted half-way would render a partial board that looks exactly like deleted rows.
> Round-trip proven on 61 rows: 61 in, 61 distinct addresses, 61 out, every field identical, and
> two ids that slug identically (`Q-6/7` and `Q-6-7`) still get two documents.

| ship | what it closed |
|---|---|
| **v2435** | the page published which tab is showing, and `tasks_freshness` became a gate |
| **v2436** | ONE COUNT HAS ONE PLACE — the eagle panel said 9 need-you while the server said 7, on the same rows in the same second. `/api/eagle` returned raw rows so the panel re-derived with the rule v2284 abandoned |
| **v2437** | the console could not say what was wrong, **and it leaked children** |
| **v2438** | **THE AUDITOR READ THE WRONG FUNCTION AND TEN LANES PASSED ON IT** |
| **v2469** | five DOM probes that each measured something ADJACENT to the question, folded into one helper file with the failure that produced each |
| **v2470** | a quote is not a safeguard until something checks it — the page can now be asked whether a quoted string is really on it. ⚠ Found on its FIRST real use: the check loaded the page fresh and so answered about a DIFFERENT page state than the screenshot it was judging. `__quotedIn(s, capturedText)` takes the text captured WITH the picture |
| **v2471** | **THE PAGE HID ITS OWN NAV FOR A RAIL THAT WAS NOT THERE** — `?engine=1` is written only by the console's `#tvd-eng` iframe and hides the whole tab row on the theory that the console header replaces it. Nothing checked the document was in that iframe, so top-level he had **0 of 19 tabs** and an empty header band. The class now requires `window.top !== window.self`. Restoring the row exposed three more: two empty cluster frames, a 144px gutter under two fixed overlays, and the MAIN/LADDER toggle painted over at the same z-index and not clickable. REG-443 · guard `tv/test_app_ctx_nav.py` (RED on HEAD, green on the fix) |
| **v2472** | **THE DELETER NOW HAS EVIDENCE, AND STILL WILL NOT OPEN** — A2 step 4. `prune.arm` sat at n=0 UNPROVEN; `tv/prune_wilson.py` attempts 42 states where `retention_may_act()` must refuse (every spelling of OFF 18/18 — v2082's scar — plus unconfirmed world, a world check that raises, and a wrong-shaped drift answer, 8/8 each). **42/42, wilson 0.916 vs bar 0.839, and the lock still reads LOCKED**: kinds_bar 1.8 against sabotage 1.0, so the one door with no undo will not open on a single kind of look. Red-proven; `_Env` refuses at write time to set the switch to anything that is not OFF |
| **v2473** | **HE CLICKED LEDGER AND THE PANEL BURIED ITS OWN WAY OUT** — `#ledger-out` rendered **3224px into a 705px rail**, taking it to 5114: 4.6 screens between him and every control below, ADVANCED included. Five panes had no cap, not one. Also: the FLEET LANES had been reading UNKNOWN because a memo key folded every tally value with `.get("total")` and the tally is an **envelope** (`ok` bool, `why` None, `at` int, `source`/`profile` str) — every real call raised and the heart printed the exception where the lanes belong; and the shared renderer's error branch hardcoded "the chronicles" so the FLEET section printed a row by that name. Plus the three v2471 review findings, two of them holes in a guard written the same morning. REG-443 guard hardened + `tests/v2473_engine_driven_nav.spec.ts` asserts the law on a rendered page |
| **v2474** | **#135 — THE DAILY PICK VANISHED WHEN THE GRAIL WALL RAN OUT.** The chronicle counts the game's 403 rows while the wall offers 398 names, so `complete` never becomes true; with nothing left to hunt no pick was written and `dailyCreateAi` fell past both arms to `removeItem` — wiped, every day, for good. Measured through the real page: 398/403 → WIPED, 10/403 → unchanged, 403/403 → unreachable. Guard `tests/v2474_daily_pick_exhausted.spec.ts`, both directions |
| **v2475** | **THE RENDER GATE COULD NOT SEE ITS OWN COVERAGE SHRINKING** — the last item owed under STILL OWED BY ME. `console` went 3/3 → 2/2 and re-baselined silently. `tv/render_coverage.json` is a ratchet (coverage may rise, a drop fails), blessed at 285 node-measurements across 9 targets × 5 widths; blessing refuses on a partial run and merges rather than replacing. ⚠ It stops the NEXT drop; it cannot recover the one that already happened |
| **v2476** | **THE SAME ENVELOPE CRASH, ALIVE IN THE SIBLING FILE** — the review found `roster_routes` carrying the identical line v2473 fixed in `fleet_routes`; `roster_route_state()` was returning ok:False on his console. ONE builder now (`chronicle_routes.tally_memo_key`), quoted by both, verified identical — all three route sets derive 3/3/3. **Plus the disk**: my own review agents wrote 20.5 GB in four minutes and ENOSPC'd the machine; render_check's Chrome profile is now temporary (it had reached 1.4 GB) and `tv/safe_copy.py` makes the copy impossible (5,865 MB → 43.7 MB) |
| **v2477** | **THE INBOX HEIGHT BUDGET GUESSED WHERE THE PANEL STARTS** — a hardcoded header offset against a header that moves. `--inbox-top` is now published by an observer that measures the real thing |
| **v2478** | **THE GATE COULD NOT TELL SCROLLED-OUT FROM COVERED, AND I TUNED A LAYOUT AGAINST IT** — the exemption tested the element's rect instead of the SAMPLED POINT, so a healthy panel read as clipped and I moved real CSS to satisfy a false reading. Two of my own assertions were refuted by measurement before they shipped (the dock is 132px; sticky `bottom` was inert) |
| **v2479** | **FOUR GUARDS THAT COULD NOT FAIL, AND ONE FALSE MEASUREMENT I HAD WRITTEN DOWN** — tautological assertions satisfied by the function's own name, plus a docstring claiming import-safety that an AST walk refuted |
| **v2480** | **FOUR COPIES OF ONE TAB VOCABULARY, AND TWO OF THEM DISAGREED** — `ct.detect()` says `unique`, the model says `uniques`; each resolver matched its own producer, so the same tab resolved on one side and not the other. ONE alias map, quoted by both. Gate 91 |
| **v2481** | **THE DISK GUARD WAS OFF ON THE ONE COMMAND SHAPE THAT CAUSED THE DISK-FULL** — REG-444·450, from a 41-agent review of my own v2474-v2479 guards (36 raised, 26 refuted, 8 distinct survived). `safe_copy`'s 4 GB floor was inert whenever the destination's PARENT did not exist — the exact invocation its own docstring recounts as the disaster. Also: `--force` parsed and dropped; a fixture that screened only the top level while the real call carried the 5.8 GB reel store; a Chrome-profile guard reading an ASSIGNMENT instead of the argv; coverage refusals counted as render failures (negative clean count, both "nothing established" exits skipped); a COMMENT still answering for the framing law (1,019 of 4,749 survive the stripper); and a ratchet never JOINED to the verdict |
| **v2482** | **THE HEART PRINTED ARITHMETIC THAT WAS NOT TRUE** — `prune.arm · 42/42 refused · 0.916 < 0.839`. The sign came from the lock's STATE, not the numbers; it CLEARS its bar and is held by CONFLUENCE (1.00 against 1.80). Guarded by **J15**: if the panel prints `a ≥ b` then a ≥ b. Also `n=0` meant two things — `vault.forget` has no refusal path BY DESIGN and can never be sabotaged, yet read as an owed harness; the distinction died TWICE on the way to the screen, in a status whitelist and again in the renderer. ⚠ REG-453 was found by a COLD EYE on the pixels: connectors struck through two digits so `42/42 · 0.916` rendered as `4/42 · 0.816`, and my overlap gate compared text to TEXT while a `<path>` did the crossing |
| **v2483** | **TWO RIGHT NUMBERS THAT READ AS A CONTRADICTION** — the heart printed a roster count beside a chronicle total for the same tab with nothing saying they measure different things. The second eye REFUTED my first fix: labelling the quantities was not enough, because a reader can see two words differ and still not know the difference is deliberate. Also a footer claiming "All 3 read the same" under three differing counts — it meant SHAPE |
| **v2484** | **ONE TAB, ONE NUMBER, ON EVERY SURFACE THAT PRINTS IT** — HIS RULING: *"sync and match them obivously.. no reason to have this gap"*. Three route sets read three producers (runeword 105/99/99, unique 398/403/403) and every number was right. All three now quote `tv/route_totals.py`: runewords **99** (his v2192 ruling, and independently the RUNEWORD_TIP catalogue size), sets **135 pieces** across 34 sets, uniques **403** (his v1751 ruling from the game files). The roster lengths are kept and said out loud as ODD ONE OUT rather than winning a column, and the THIRD route set — computed and rendered nowhere — is joined. ⚠ Two self-catches: the set walk returned a confident **81** because the third declaration quotes its key, and a cache key folded every mtime into `max()` so touching `bible.html` left it byte-identical in all three modules. 15 guards, none naming 99/135/403 |
| **v2485** | **A1 — THE HEART CALLED A JOB "WORK OWED" THAT COULD NEVER LAND.** FLOWING was unreachable: `scored` is keyed on ORGAN ids, the lookup uses LANE names, and the two vocabularies are disjoint. Measured — score every organ 1.0 and it stays FLOWING 0; score every watcher and 11 turn at once. The row now derives whether a score could ever land. ⚠ The honest half: no lane scorer exists yet, so FLOWING is still 0 — it just stops lying about why |
| **v2486** | **HIS OWN CI CAUGHT THREE LYING DEFAULTS, ONE IN A RATCHET.** Routine M red, swallow ratchet 74→77. A failed read of `control_ui.html` became `""`, so a lane reported "the screen does not say what it is counting" — a fault blamed on the UI. And an unparseable width was recorded as `0` **into the map `--bless` writes as the coverage FLOOR**, so it could have lowered its own ratchet. ⚠ My first diagnosis was wrong and the fix changed nothing; asking the census WHICH sites was one command |
| **v2487** | **THE TWELVE ROUTES PROVE THEMSELVES — HIS RULING.** `tv/route_wilson.py` removes what each lane claims to have found and counts whether it noticed; 9 routes in the SAME `self_arming` table, same `score()`, same ledger, declared in `PROVES`. A valve earns permission to ACT, a route earns trust in the NUMBER IT PRINTS. **HARD MODE** (leave the evidence, break its meaning) found two real defects easy mode called perfect: `source` was `isfile()` so a **zero-byte bible.html read as healthy**, and `declared` matched an **emptied** `const ITEM_VALUE = []` and a name left in a comment. After both fixes **48/48 across 9 routes**. Plus **HARDENED**, a state above the bar (wilson ≥ 0.90 AND confluence ≥ 2.50) — nothing has reached it, and `miniauto.run` shows why: 55/55 refused, all one kind. ⚠ The harness was proven able to catch a planted always-ok lane BEFORE its score was believed, and made four instrument errors, each corrected before reporting |
| **v2488** | **A TASK VANISHED FROM THE BOARD BECAUSE ITS TITLE CONTAINED THE SEPARATOR.** A17's title carries a `·` and the parser split on it, so the row was never derived — and a generator that promises it never prunes cannot report a row that failed to PARSE. Coverage now counts every `## AN ·` header against derived rows; that is the only check that catches a silent loss. |
| **v2489** | **THE NINE ROUTES ARE DRAWN ON THE HEART, DERIVED — NOT LISTED.** His words: *"not draw it needs to derive / live / for real"*. The routes section reads `d.routes` at render time on the same arithmetic as the valves. |
| **v2490** | **A TASK VANISHED AGAIN, AND THE STORYLINE WAS INVISIBLE.** `sectionOrder` 2001-5001 sorted the new pending→progress→completed storyline BELOW the existing 0-11 sections, so the structure he asked for was published and unreachable. Renumbered negative. |
| **v2491** | **A3 — THE EMPTY TABLE WAS NOT EMPTY, IT WAS UNJOINED.** 44 surfaces × 4 organs measured. The holes are three different things: 9 MISNAMED (the organ watches it under another name), 1 organ UNKNOWN everywhere, the rest genuinely ABSENT. Reporting a MISNAMED cell as ABSENT is how the table came to look empty. |
| **v2492** | **ARCHITECTURE: ONE CONCEPT, MANY RENDERINGS.** `tv/one_name.py` — three resolvers disagreed on 6 of 9 inputs, so the console had five local alias maps and no source. One table, every surface quotes it. |
| **v2493** | **THE FIRST LOCAL RESOLVER RETIRES INTO `one_name`**, measured behaviour-neutral before the swap (132 cells agree, 0 differ). ⚠ Its commit ALSO published a wrong claim, corrected in v2495. |
| **v2494** | **A NINTH RESOLVER MAY NOT APPEAR UNNOTICED.** A ratchet over 8 known `(file, name)` pairs, scanning by SHAPE rather than by a list of names. |
| **v2495** | **I PUBLISHED A WRONG CLAIM AND A COLD REVIEW REFUSED THE INFERENCE BEHIND IT.** v2493 said A1 was *"proven NOT a naming problem"* from 0 joinable pairs. The review: *"zero joinable pairs only tells you the resolver, as currently configured, found no matches"* — and one command found `shadowWatch == tvd-shadow-watch`. **The 0 measured my own function's reach, not the world.** A1 is PARTLY a naming problem: 1 of 7. |
| **v2496** | **A3 — THE DOCTOR ANSWERS NOW, AND THE TABLE REFUSES TO CALL AN UNMEASURED CELL A HOLE.** `console_doctor.report()` names all 34 checks in 0.000s with the network booby-trapped — it could not be a thin alias for `run()`, which posts to `/api/board_ownership` and **evaluates JavaScript in the window he is looking at**. ⚠ Three joins, not one: the matrix was missing the `check` synonym and would have silently reported an EMPTY name set; and even then ABSENT was a verdict nobody had earned, because the doctor names CONCERNS and the surfaces are CODE OBJECTS with ZERO overlap. ⚠ My first guard PASSED the sabotage — it asked the module whether the module was right. |
| **v2497** | **A3 DONE — NINE MISNAMED CELLS WERE ONE DROPPED QUALIFIER.** `_corr()` flattened three route modules into one set of bare names and discarded which lane each came from. All 9 COVERED, and exactly those 9. ⚠ The first form joined only SIX; the three holdouts named a real split — chronicle/roster spell their routes SINGULAR, fleet PLURAL — logged as REG-470 and deliberately NOT absorbed silently in the reader. |
| **v2498** | **A COLD REVIEW FOUND DEAD CODE INSIDE THE FIX I HAD JUST SHIPPED.** The camelCase substitution in `_shape()` inserted a `-` the next line deleted; zero inputs changed result. It also refused *"not a fuzzy match"* — `user_id` and `userid` collide — so the honest version is a measurement held as a ratchet: 3 collisions across 100 live names, all correct. One finding REFUTED with a proof. ⚠ And my own new test never ran: `cat >>` appended it below the `__main__` runner — **8 tests, 0.004 seconds, GREEN**. The clock was the tell. |
| **v2499** | **THE BOARD IS A BUILD OUTPUT, AND IT COULD NOT HOLD HIS OWN DECISIONS.** He retired A6 and hibernated A18/A20; re-running the deriver the same hour filed all three back into PENDING, because `_classify` knew five states and none was *"he decided not to"*. Three more defects surfaced fixing it: a GLOBAL topic index that numbered VISUAL onto another stage's base, stage bases 1 apart where a stage held two topics, and a ruling marker matched ANYWHERE which retired A1 for merely *mentioning* a scope cut — the count was the tell. ⚠ And my first cut added a SECOND state table while fixing two sources disagreeing. 5 sabotages, 5 RED |
| **v2500** | **THE CENSUS HAD A SOURCE THAT NEVER ONCE ANSWERED.** It read `heart.snapshot()`, which does not exist, so behind a `hasattr` guard that source contributed ZERO names on every run since it was written — and a sabotage disabling it went GREEN, because every reviewed collision came from elsewhere. A guard must fail on its own REACH. ⚠ And my v2495 A1 correction used the same dead call, fell through to a fallback list I had typed into the probe, and published it as a fact about his console. Measured properly: **2 of 11 lanes** are named by an organ under another spelling, not 1 of 7 |
| **v2501** | **A DIFFERENT FAMILY ARMED THE DELETER WITH A VALUE THAT MEANS OFF, AND THE FIFTH LOCK OPENED ITSELF.** `TV_AUTO_PRUNE="<zero-width space>0"` ARMED an unattended irreversible deleter; so did `offf`, `disabled`, `flase`, while the code's own comment said *"A typo is not permission"*. v2082's scar in a new costume — the UNRECOGNISED arm was the permissive one. OFF holds, ON proceeds, UNSET still proceeds (his ruling, pinned), SET-but-unrecognised now holds. **`prune.arm` opened itself: 48/48 · wilson 0.926 ≥ 0.839 · kinds ['cross-family','sabotage'] = 1.80 ≥ 1.80** — A2 is 4/4. ⚠ Nothing was armed: `may()` is never called anywhere |
| **v2502** | **THE REACH CHECK I ADDED TO STOP A BLIND CENSUS WAS MEASURING THE WRONG QUANTITY.** It scored each source by a DELTA: `heart.vessels` HOLDS 46 names and recorded 12, because 35 of them ARE the surfaces — so a healthy source could report 0 purely because another ran first. Each source is measured by its own set now; pool unchanged at 111. ⚠ Blank names also counted as contribution and my first fix did not catch it — sabotaging the filter left the file GREEN |
| **v2503** | **THE PRINTER ZONE'S ACCEPTANCE TEST, AND THE ZERO AT THE HEART OF IT MEASURES A FILTER.** The contradiction A4 was born from returns ZERO — because **not one of the 30 seals satisfies the extraction contract** (22 fail on the same fact, `name`; 8 predate it), so no reel can be judged disposable and the contradiction is structurally UNREACHABLE rather than absent. `name` only ever appears in a hover tooltip, so a grid-only reel can never satisfy the contract and is permanently outside what the printer may act on — that is the guard working, and the honest answer to how much of the cluster is real work. 5 sabotages, 5 RED |
| **v2504** | **THE REACH HELPER TESTED ONE VALUE AND STORED ANOTHER.** `" foo "` passed the emptiness test and entered the pool PADDED — and since `_shape` deletes whitespace it would collide with its own trimmed form as a NEW unreviewed collision. ⚠ Sabotaging it back went GREEN: nothing in his stores is padded today, and `_keep` was a CLOSURE nothing could call, so the law had no test. Hoisted and checked on constructed input. ⚠ `SOURCES` was also a promise about reach that nothing checked. ⚠⚠ And the hoist left the rule WRITTEN TWICE, unreachable below a `return`, in the file whose whole subject is two sources disagreeing |
| **v2505** | **A10 — THE FISH DOWN THE STREAM, and the measurement misled its own author first.** 12 reels reporting RELEASABLE beside a frame authority refusing every seal reads exactly like a defect. It is NOT one — v2314 ruled two granularities correct and WITHDREW the collapse, because it would have stopped the prune firing on every reel he owns. **And nothing on any screen said so** — that is the gap A10 names. `tv/reel_river.py` reports every stage WITH THE DECIDER AND THE QUESTION: 40 reels, 28 swept, 12 releasable, frame door no on 15 / UNASKED on 25, **0 gaps**. A gap is two deciders answering the SAME question differently |
| **v2506** | **THE FIX I SHIPPED ONE VERSION EARLIER DID NOT CLOSE THE HOLE IT WAS WRITTEN FOR.** The undeclared/unrecorded pair compares KEYS, so a source that contributes names and records nothing was invisible to both — confirmed by construction. The sources record their SETS now and the pool must equal the union of what the declared sources supplied. ⚠ Refuted with the interpreter: the `if names:` guard is not a no-op, it prevents a crash on an organ that cannot be asked |
| **v2507** | **A7 MADE CHECKABLE — and two attempts to measure writers both measured the instrument.** A filename-adjacency grep returned 0 writers for all four reel stores; so did an AST walk resolving path constants. Both zeros measured MY INSTRUMENTS, so A7 is not scoped on a number I do not trust. `tv/store_owners.py` makes the codebase's own prose declarations checkable: one OWNER per store, every other module a reader WITH A REASON, a new toucher fails until argued in. ⚠ It reports COUPLING, not writes, and says so. ⚠ The registry CAUGHT ITSELF on its first run |
| **v2508** | **THE ORPHAN CHECK LET AN UNDECLARED SOURCE ACCOUNT FOR ITS OWN NAMES.** It summed ALL of `reach.values()`, so a fourth key's names landed in `accounted` and the check went quiet. ⚠⚠ My first two guards for the fix were BOTH WORTHLESS and the sabotage said so — one a tautology that recomputed the rule inside the test, one asserting something that cannot happen |
| **v2509** | **A14 — A COUNTER THAT ONLY GOES UP NEEDS A STORED PEAK.** `console_doctor` already names what vanished, but only between the TWO NEWEST snapshots, so a finding survives exactly as long as nobody takes two more. ⚠⚠ THE MODULE'S OWN FIRST ACT WAS THE BUG: `seed()` recorded the LATEST snapshot as the peak, which would have locked an existing loss in as its own high-water mark. Seeds from the highest across all 60 snapshots now. ⚠ One sabotage PASSED at first — the re-seeding guard only matters once the snapshot proving the high is ROTATED AWAY. **Measured: 60 snapshots, ZERO drops — it ships GREEN, insurance not a live fix**, and the window BEGINS AFTER the 2026-08-28 loss |
| **v2510** | **EXTRACTING THE RULE PROVED IT WORKS, NOT THAT ANYTHING USES IT.** A cold review caught that the helper test would pass identically against an inline duplicate at the call site — the same unjoined shape the extraction was meant to escape. The guard now swaps the rule at runtime for one reporting a sentinel and REQUIRES the census to notice. ⚠ Also: a bare string pool would have compared CHARACTERS |
| **v2439** | the panel said what was wrong and buried it under a number nobody can act on |

### ✅ CF-1 — CLOSED, and the premise was FALSE

Filed as *"chronicle and vault both stopped doing work hours ago"*. **Neither lane ever stopped.**
Measured against the live console: chronicle 401 sessions / **owed 0** / 19.9 h, vault 30 / **owed
0** / 23.0 h — both well inside their 48 h threshold, both correctly idle. Two real defects hid
behind the wrong label:

- `console_doctor` renders `evidence[:2]`, and `health_engine` built it lanes-first — so the panel
  printed two sentences describing a **healthy** lane under the word `missing`, and dropped the one
  that named the fault. Fixed at the producer; the consumer cannot know which of three is deciding.
- `lane_health.divergence()` was **always-red a second time**. v2302 fixed the dialect; the same
  defect survived one level up, differencing two LIFETIME ledgers against nothing on disk:
  371 "diverged", of which **346 have no footage at all** and can never be sealed by any amount of
  lane work — a red that grows every time footage is correctly pruned. Now `actionable 25 ·
  historyOnly 346`, and it can finally report ALIGNED.

### ✅ B-86 — CLOSED, and it was ten times worse than filed

`auto_scope._fn_source` used `inspect.getsource`, which slices the file ON DISK at the RUNNING code
object's `co_firstlineno`. His console runs the build it booted with while the tree moves under it,
so **11 of 11 lanes resolved to the wrong function**:

    _ledger_backup_loop  ->  _ledger_snapshot_once     _prune_loop   ->  live.sort
    _warden_loop         ->  live.sort                 _eagle_watch  ->  _eagle_once   ...and 7 more

One visible false red — and **TEN SILENT PASSES** about functions nobody declared. `tvd-rolling-prune`
is the only lane that can remove his footage and it was being audited against `live.sort`.
**Unswept sibling:** `control_app._app_ver()` carries the identical paragraph and was fixed at v2155.

### ✅ Also closed today

| # | outcome |
|---|---|
| **B-70** | REFUTED — the extraction lanes finished; both owed 0 |
| **B-81** | ALREADY FIXED at v2400, 2h21m after the fault fired. The wolf-crying now lives in the eagle check, whose N is **1** |
| **B-82** | CORRECTLY REFUSED — folding the orphan frame would mint a second session id for one recording |
| **B-63** | **NOT defects.** session-901 is an allowlisted designed truncation (the v2221 64px reserve); forge-901 is an honest 0% over a fixture that forged nothing |
| **Q-6/7** | two dead sessions still claiming "working", reconciled with the reason |
| **A11** | census run: **30 thread targets · 11 supervised · 8 UNWATCHED loops · 2 unclassifiable** |
| **A12** | earned its keep first time out — census 19 vs `BLUEPRINT.md` 18, a loop unsupervised since v2433 |

### 🔓 NEW — the lock that unlocks itself (his ruling, 2026-09-02)

> *"a lock until it automatically unlocks with a que for wilson score. arithmetic as you see."*

`tv/self_arming.py` replaces the hand-flipped `_PRUNE_SAFE_TO_RUN`. **k and n count SABOTAGES
ATTEMPTED and REFUSALS EARNED, never agreements** — an invariant that always agrees may be perfect
or INERT, so a lock fed by an agreement rate opens *because nobody tested it*. Wilson AND confluence
both. His order enforced. No override parameter. And **Wilson is now the fifth organ of the heart**:
any `health_engine` row can carry a score, computed in one place.

⚠ Every lock currently reads **UNPROVEN** — that is work owed, not a fault, and the console says so
in those words.

### ⚠ STILL OWED BY ME, named rather than buried

- **#135** — the daily-pick fingerprint. Its row says the undone-ness has no single string; I will
  not write an anchor that matches the wrong occurrence.
- **The render gate does not cover what I changed.** The `console` target went 3/3 → 2/2 when a
  control was hidden and **re-baselined silently**; the new vault lock chip has no target at all.
  Unmeasured reads identical to clean in a green run.
- **A2's next step:** the sabotage harnesses already catch 3/3 and 4/4 and **throw every result
  away.** That is why every score is null — not because nothing was tested, but because nothing was
  recorded. Printer and reels first, in his order.

---

## A20 · THE RIVER, VISIBLE — ONE STORYLINE INSIDE THEATRE/SHELF · 2026-09-02 · ⏸ HIBERNATING
**Topic:** VISUAL · **Progress:** ⏸ HIBERNATION — his call, 2026-09-03: *"put it aside.. and in hibernation mode.. until every task first is done before it.. defer it regardelss what ever you recommend.. not drop for sure"*. **DEFERRED, EXPLICITLY NOT DROPPED.** Build A10 (the fish down the stream) first — it gives most of the same diagnostic power in text. **CONSEQUENCE ACCEPTED:** routing is diagnosed textually until this wakes up. Nothing about accuracy changes


> *"the SHELF/THEATRE should be one section and tab in general just additive within one or the
> other.. and also there the structure and everything meaning it should be STORY LINE STRUCTURED..
> from where the reel gets received and then eventually gets processed and through the 3d filter and
> templates that route the garbage to the garbage and down the stream litteraly visually showing
> this.. the reels coming in show they come in.. and section down is the sections the reels start
> getting filtered through and at the bottom is an organized END ROUTE for each reel down the stream
> it goes — that way we can SURGICALLY FIX anything not correctly routed.. like a game.. like a sort
> of tetris.. the last section where the garbage is goes straight to garbage and inbetween there is
> the extraction area and processing.. and afterwards ALSO go to the same route end which is
> garbage! and pruned and optimized and deleted — eventually THE END ROUTE IS THE SAME, ALL UNIFIED.
> The difference is WHERE those reels get processed through that same filtered and template based
> coding."*

### ★ THE INVARIANT HIDING IN THAT SENTENCE, AND IT IS WHY THIS IS A GATE AND NOT A DIAGRAM

**Every reel reaches the SAME terminal. Only the path differs.** Garbage goes straight there;
gold goes through extraction and processing and arrives there too. That makes the picture
*falsifiable*:

    a reel that never arrives at the terminal is a ROUTING DEFECT, and the screen names which
    stage it is stuck in

That is the difference between a drawing and an instrument. A pretty pipeline that cannot say
"this reel is stuck at stage 3" is decoration; one that can is A10's fish-down-the-stream made
visible, permanently, for every reel at once.

### THE SHAPE — top to bottom, and the vertical IS the story

    ┌ RECEIVED ─────────  reels arriving, as they arrive
    │
    ├ FILTERED ─────────  the 3D/4D printer's stages · the templates live INSIDE the routing (A8)
    │                     the 10–15% law throws garbage out BY DEFAULT here (A9)
    ├ EXTRACTION ───────  the paid reads, the processing
    │
    └ TERMINAL ─────────  ONE end route: pruned · optimised · deleted. Everything lands here.

⚠ **DERIVED, NEVER DRAWN — the same rule the heart carries.** Every stage's contents come from the
real routing state on read. A hand-maintained pipeline picture is a map that drifts from the
territory, and this repo already paid for that when `BLUEPRINT.md` went stale and a gate graded the
last build.

⚠ **AND IT MUST NOT BE ABLE TO SHOW AN EMPTY STAGE AS A CLEAN ONE.** A stage with no reels in it is
either "nothing is owed" or "nothing reaches this stage" — opposite facts, and the second one is the
routing defect this exists to find. They must render differently.

**PREREQUISITE:** the printer/river itself (A4 · A15) still has to be architected. This is its
surface, and building the surface first would be a picture of something that does not exist.
Shelf/Theatre being one door is already done (v2440–v2441).

---

## A18 · THE D2R MACRO — HE IS THE CALIBRATION SOURCE · 2026-09-02 · ⏸ HIBERNATING
**Topic:** CAPTURE · **Progress:** ⏸ HIBERNATION — his call, 2026-09-03, same ruling as A20: aside until everything before it is done, **deferred not dropped**. **CONSEQUENCE ACCEPTED:** the hover stays manual. That is labour, not correctness — no accuracy is lost by waiting


> *"for the hover automatic MINI with grok bot it aint gonna work, i thought of another clever
> idea.. like MACRO ISSTA and MACRO FIBI we created repos based on my movements cursor. this is the
> same.. we can construct a DIABLO II MACRO — i can be the one doing the calliberating to the
> system :) you just hook it up with like the same style demonstration demo test just like we have
> for MACRO ISSTA.. its like designed to record me then we can test it and sync it until perfection"*

**WHY THIS BEATS THE ROUTE IT REPLACES, and it is not a matter of taste.** The Grok-Bot hover plan
needed two things that were never true: synthetic pointer events (which on macOS need Accessibility,
and without it `CGEventPost` SUCCEEDS SILENTLY while moving nothing), and a known stream transform
(the Windows game runs in a browser over a cloud stream, so screen space is game space times a scale
and offset nobody has measured). A recording of HIS OWN hand needs neither. He is on the real screen,
and the recording IS the ground truth rather than something derived through an unmeasured factor.

It is also his own ruling applied: *"anything done manually by a human is proof and witness enough."*

### WHAT IT PRODUCES — the thing `screen_point` has never had

Each recorded hover yields one triple:

    (col, row)  ->  screen point he actually hovered  ->  the item the tooltip actually named

That is ground truth. Today `hover_wilson.probe_coordinate` round-trips `point_of_cell` through
`cell_of` and proves **those two functions agree with each other** — never that either agrees with
Diablo. `human-eyes-harness` names it as the canonical instrument-agreeing-with-itself, and this is
what stops it being one.

⚠ And in Wilson terms that matters more than it sounds: an instrument that only agrees with itself
is an INERT invariant. It would score beautifully on agreements and prove nothing. A recorded human
hover is a genuinely INDEPENDENT KIND of evidence, which is exactly what `confluence` needs so a
score is not thirty copies of one fixture.

### THE SHAPE — copy MACRO ISSTA, do not reinvent it

Record → replay → diff, with the demonstration-demo test style that repo already uses. Sync until
the replay names the same items he did.

⚠ DO NOT bake any coordinate constant from a single session. Measure, report raw, decide after — a
number fitted to one recording is a stream-shaped or resolution-shaped constant wearing a general
name. [[label-outlived-referent]]

---

## A19 · MINI AUTO CARRIES A LOCK — BADGED, NOT ENFORCED · 2026-09-02 · SHIPPED
**Topic:** ARCHITECTURE · **Progress:** SHIPPED · MINI AUTO carries a lock, badged not enforced


> *"i want it not enforced... i want it badged... my point was i want it KNOWN on the console is
> all. a visual stamp is fine. and obviously a logical coding to it with wilson via connected to
> the heart for real."*

`miniauto.run` is declared in `tv/self_arming.py`, scored the same way as every other lock, and
rides `st.selfArming` to a chip on the MINI AUTO card. **Nothing calls `may()` to block the button,
and that is deliberate rather than unfinished.** The point is not to stop him — it is to stop the
console PRETENDING. It sits at step 1 of his order because MINI AUTO drives the pointer over the
stash and films the tooltips: that IS the printer and the reels, which is where he said Wilson
starts.

---

# 🏛 THE ARCHITECTURE ASKS — recovered 2026-09-01, and they were NEVER in the 22

**These are the ones that went missing.** The numbered list was the DEFECT queue — P1s, briefs,
Grok items. Everything below is something Konyo asked for directly, in his own words, as a system
to build. None of it had a number, so none of it survived. Recovered by extracting all 993 of his
turns out of the 688 MB transcript.

Quotes are verbatim, including the typing. They are the spec.

## A1 · SELF-PROVING GAPS, EVERYWHERE ROUND THE CONSOLE  · 2026-09-01 11:00
**Topic:** ARCHITECTURE · **Progress:** 1/3 · **MEASURED PROPERLY IN v2500, and this claim has now moved twice.** v2493 said A1 was "proven NOT a naming problem"; v2495 retracted that citing `shadowWatch == tvd-shadow-watch` — but that probe called `heart.snapshot()`, which DOES NOT EXIST, got nothing, and fell through to a fallback list of names I had typed into the probe myself. ⚠ I measured my own fallback and published it as a fact about his console. **The real numbers, against `heart.vessels()`: 11 lane names, 65 organ-published names, ZERO exact matches, and 2 of 11 lanes matched by the resolver** — `tvd-shadow-watch` ← *shadow watch* (console_doctor) and *shadowWatch* (health_engine); `tvd-version-drift` ← *version drift*. So A1 is PARTLY a naming problem, 2 of 11; the other 9 lanes have no organ publishing anything under their name, which is the missing SCORER exactly as this task always said. It only became measurable because v2496 gave console_doctor a report(). ⚠ And the vessel→watcher link needs NO resolver: 11 of 21 vessel rows already name their own watcher. · v2485 made the heart stop calling unreachable work 'owed'. **MEASURED v2521 — the scorer is not missing WORK, it is missing EVIDENCE.** Only **2 of 11** watcher lanes have anything published under their name (`tvd-shadow-watch`, `tvd-version-drift`); the other 9 have nothing. ⚠⚠ AND NAMING IS NOT SCORING: `health_engine` reports `shadowWatch` **state=ok** while its own line says *"the shadow reader is switched OFF, so nothing is watching for the game"* — so a scorer built on organ states would have reported a SWITCHED-OFF LANE AS FLOWING, and it would have looked like A1 finally working. `ok` is a verdict on the CHECK, not evidence that the lane ran. **THE QUESTION (his call):** should each watcher lane write a HEARTBEAT when it completes a pass, so FLOWING means *this lane did work recently* — or should FLOWING stay unreachable until there is something truer to score? Not built either way. ⛔ **SCOPE CUT 2026-09-03, his call — "scratch it off the list":** *the four organs on every surface* is OUT. A3 measured the ground truth — 44 surfaces, most of them internal loops like `_bridge_prober` and `_chron_autoread_loop`; four organs each is **176 wirings** for no gain. What replaces it: declare in code which surfaces can **lose data or show him a number**, wire those, and mark the rest out of scope WITH A STATED REASON, so the matrix stops being a 44-row guilt list. Denominator moved 4 → 3

> *"self-proving gaps i want taken care of everywhere all round the console i want this logic and
> its own logic coded proving itself! and if it drifts it gets flagged accoridngly and designed
> like we designed to either get fixed or we fix it and the doctor it to be watchdgoged and
> connected to the heart to fix iteself by hardcode design once everything is fixed and locked in
> maybe not just yet the self healing... but in the future no reason for not"*

The flagship. Every gap on the console carries its own proof, flags its own drift, and is wired to
THE HEART (eagle eye · watchdog · corroborator · doctor). ⚠ **Self-healing is explicitly NOT yet** —
he said "maybe not just yet". Build the proving and the flagging; leave the self-repair for later.

## A2 · WILSON EVERYWHERE — and make it actually mean something · 2026-08-30 09:25 + 09:30
**Topic:** ARCHITECTURE · **Progress:** 4/4 ✅ · **v2501 — `prune.arm` OPENED ITSELF**, the last lock with evidence still to gather: `48 of 48 refused · wilson 0.926 ≥ 0.839 · kinds ['cross-family','sabotage'] = 1.80 ≥ 1.80`. The second KIND came from handing `retention_may_act` COLD to a different model family and asking it to design attacks — three refused, and one LANDED: a zero-width space before a valid OFF value ARMED an unattended irreversible deleter, as did `offf`, `disabled` and `flase`, while the code's own comment said *"A typo is not permission"*. Fixed (REG-481/482); his default-on ruling pinned by its own test. ⚠ Nothing was armed — `may()` is never called anywhere, the locks are badges. ⚠ REMAINING for a later pass: nothing is HARDENED (needs a THIRD kind, confluence ≥ 2.50); `vault.forget` is UNPROVEN by construction and always will be. · v2444-v2472 banked the five valves (3 of 5 open, none by hand); v2487 added the 9 ROUTES on the same arithmetic, 48/48 under hard mode. Remaining: nothing is HARDENED — needs a second independent KIND, which is prune.arm's only gap

> *"YES wilson score it .. thats why i keep saying put this system everywhere.. do a full audit
> around the entire console to where WILSON can be added"*

⚠ **AND THE AUDIT ALREADY FOUND THE REAL DEFECT:** *"Wilson isn't currently doing anything
different. It's a second spelling of the same rule."* `confidence.shadow()` already accepts tags
and tiers, `confluence()` is built, **the wiring passes them — and the floor makes them
irrelevant.** So the job is not "add Wilson in more places": it is make the score take CONFIDENCE
and CONFLUENCE into account instead of counting clean looks, so one 0.95 look corroborated by the
roster can ground where three 0.60 looks cannot. The curve: 1/1 → 0.207 · 3/3 → 0.438 ·
6/6 → 0.610 · 12/12 → 0.757.

## A3 · UNIFY THE SURFACE × CAPABILITY MATRIX · 2026-08-30 ~17:20
**Topic:** ARCHITECTURE · **Progress:** 3/3 ✅ · v2497 MADE THE JOIN — the 9 MISNAMED were ONE dropped qualifier: `_corr()` flattened three route modules into one set of bare names and threw away which lane each came from. All 9 are COVERED now, and exactly those 9. ⚠ The first form joined only 6 — the 3 holdouts named a real split: chronicle/roster spell their routes SINGULAR, fleet spells them PLURAL. That is logged as REG-470 and is NOT fixed, only stopped from corrupting the measurement; the real fix is the one_name cut-over reaching fleet_routes. · v2496 made the doctor's column ANSWERABLE — `console_doctor.report()` now names all 34 checks without touching the window he is looking at (`run()` posts to /api/board_ownership, which evaluates JS in his live board), and the matrix learned to read `check`. ⚠ THAT ALONE WOULD HAVE MADE THE TABLE LIE: the doctor names CONCERNS and the surfaces are CODE OBJECTS, zero of 34 resolve to any of 44, so the column filled with 44 confident ABSENT cells. An incomparable column now says UNKNOWN with its reason, and the summary states how many organs its verdict rests on (1 of 4). REMAINING: make the join so the 9 MISNAMED become COVERED. · v2491 MEASURED the matrix — 44 surfaces × 4 organs, and the holes are three different things: 9 MISNAMED (the organ watches it under another name — a join nobody made, and how the table came to look empty), 1 organ UNKNOWN everywhere (console_doctor has no report), the rest genuinely ABSENT. REMAINING: make the join so MISNAMED becomes COVERED, and give console_doctor a report so its column is answerable.

> *"fix those gaps and anywhere else.. make it unified and logical and coded properly with
> watchdogged and eagle eyed and doctor and corraborotror"*

Said over a table of surfaces against capabilities that was mostly holes — `surfaces registry`
empty across every column, `stash_eye grid` empty across every column, `enlarge (crop + …)` empty,
`OCR worker` present in exactly one. Every surface gets the same four organs, or it is honestly
marked as not having them.

## A4 · THE 3D / 4D PRINTER PIPELINE · 2026-09-01 10:49
**Topic:** BACKEND · **Progress:** 1/3 · ⭐ **A10 SHIPPED in v2505** (`tv/reel_river.py`) — the acceptance test and the end-to-end probe both exist now. v2503 measured what the pipeline can act on AT ALL: 0 of 30 seals satisfy the extraction contract (22 fail on `name`, which only appears in a hover tooltip), so the A4 contradiction is structurally UNREACHABLE rather than absent and a grid-only reel can never be judged disposable. v2505 walks each reel naming the decider and question per stage. REMAINING: the unified printer itself (A7·A8·A15) — one path, templates inside the routing.

> *"we already said if this were to be procesed through our 3D printer it shouldnt matter the
> engines console and filtering and routing system should have done that already and left those
> 104 frames for extra 3D and 4D printer processing and filtering and routing so those other
> worthless frames are check and pruned out alone via templates and techniqued and filters within"*

Said about the prune contradiction — 12 reels prunable, 7 claiming "examined, nothing to take"
while the survey says they held 104 panels. **His point is that the contradiction should never
have reached a human.** The console's own filtering and routing should already have run those
frames through the printer, kept the 104 for extra 3D/4D processing, and pruned the worthless ones
by template, technique and filter — alone.

## A5 · THE SURFACE IS KNOWN AT CAPTURE — KEEP IT · 2026-09-01 10:55 · HALVED 2026-09-03
**Topic:** BACKEND · **Progress:** ⚠ **WIRED BUT INERT (v2515 + v2517)** — **the INTAKE half only.** ⚠⚠ MY v2515 CLAIM THAT THIS "stops all future loss" WAS WRONG and is corrected here: the stamp is correctly wired and **stamps 0 of 14,034 rows**, because `_sighting_loc` returns None for every one. v2517 found why — the sighting carries `reel_<session>` while the journal is keyed `<session>`, so **that gate has resolved NOTHING for a stored sighting since v2353**, the exact failure its own docstring warns about. Bridging the prefix collapsed `no_segments` 10,101 → 1,353, and resolution is STILL 0: necessary, not sufficient. ⚠ The stamper also reaches only 10,101 of 14,034 rows — 28% of the store nests differently and is silently skipped. **THE SECOND REFUSAL IS NAMED (v2519):** `lane_at` asks which segment CONTAINS the moment, and segments are the INSTANTS OF READS, not the intervals between them — measured, one session covers **3.52%** of its span and **13 of 483 frames (2.69%)** fall inside a segment. Store-wide, **8,748 of 10,101 lookups now FIND their segments and still cannot answer**. That is not a defect in the resolver; it is what containment means against instantaneous segments. ⚠ **HIS CALL:** widening it to *the nearest read* would make provenance a GUESS, and this answer feeds a door that refuses vault claims — so it is put to him rather than changed underneath him. **THE QUESTION:** should a frame captured between two reads inherit the lane of the nearest read (and within what window), or stay UNKNOWN? REMAINING besides that: widen the walk to the 28% of rows that nest differently. `_sighting_loc` has answered *where a name was seen* since v2353 and **nothing kept the answer**: measured on the live store, **0 of 14,034 evidence rows carry a persisted `loc`**, while **39 reels are named and 3 still exist — 92% gone**, so only 25% of rows could ever have it re-derived. Computed, rendered, thrown away. The stamp now runs at evidence-merge time, the last moment the reel is reliably present. ⚠ THE FIGURES BELOW WERE UNDERSTATED — 20/6/70% was the earlier reading; it is 39/3/92% now. ⚠ It cannot recover the past: a row whose reel is gone stays without a loc for ever, which is the 75%. Future loss only.
⛔ **THE REVERSE-DERIVATION HALF IS CUT** (his call, 2026-09-03: *"delete it too"*). "Prove it both
ways" only validates data already captured, and **70% of that film is gone** — 20 reels named in the
evidence, 6 still on disk. Building a reverse direction to re-check 6 reels is work priced for 20.
⚠ **KEPT, and it is the part that matters:** stop throwing the surface away at intake. That is cheap
and it stops ALL future loss. **CONSEQUENCE ACCEPTED:** the 6 surviving reels are never retro-validated.
⚠ If he meant to cut A5 whole rather than its reverse half, say so — I took the narrower reading

> *"the fact was in hand at intake, discarded, and the re-derivation needs footage that no longer
> exists … a logic both ways reverese enginnered and agreeing would also prove to fix this.. so
> connect it to the heart of the console too."*

Measured: 20 reels are named in the evidence and **only 6 still exist — 70% gone**, so the resolver
is re-deriving from film that has been pruned. Two halves: stop throwing the surface away at
intake, AND build the reverse direction so the two must AGREE. Wire it to the heart.

## A6 · ~~A GATED AI READER BETWEEN THE RETRO ANALYZERS~~ · RETIRED 2026-09-03
**Topic:** BACKEND · **Progress:** ⛔ RETIRED — his call, 2026-09-03: *"scratch it off the list"*

> **NOT DELETED, RETIRED WITH THE REASON**, so nobody re-derives it in three weeks. The console
> already has `engines corroborate` adjudicating analyzer disagreement, and the third-eye seat
> has **zero replies across 284 briefs** — an AI gate between two analyzers is a chair for
> someone who has never sat down.
> **CONSEQUENCE ACCEPTED:** if two analyzers disagree, the existing corroborator still flags it.
> What is given up is a second opinion that was not arriving.

> *"the retro analyzers need to be accurate and thorough with an extra AI reader if needed
> inbetween them as a gated and accuracy checker"*

An independent reader sitting between the analyzers as a gate, not a second opinion nobody reads.


## A7 · EVERY REEL GOES THROUGH THE SAME PATH — ONE UNIFIED LOGIC · 2026-09-01 19:0x
**Topic:** BACKEND · **Progress:** 1/2 · **v2507 made A7 CHECKABLE** (`tv/store_owners.py`): one declared OWNER per reel store, every other module a declared reader WITH A REASON, and a module that starts touching a store fails until it is argued in. 4 stores, owners retro_triage · reel_retention · vault_retro · frame_authority, every toucher accounted for (3/3/7/9). ⚠ IT REPORTS COUPLING, NOT WRITES, and says so — TWO attempts to measure writers returned ZERO for all four stores (a filename-adjacency grep, then an AST walk resolving path constants), because paths are bound in helpers and threaded through arguments. Both zeros measured the instrument, so A7 is NOT scoped on a number I do not trust. ⚠ The registry caught ITSELF on its first run. REMAINING: the actual single-writer proof needs a runtime technique (a write hook or an owner-mediated API), not a static walk

> *"all reels need to be processed the same way all unified logic"*

No reel gets a special path, a bypass, or a second implementation. One pipeline, one set of rules,
every reel. Any lane that processes a reel differently is either folded in or declared, in code,
as a deliberate exception with a reason.

## A8 · THE TEMPLATES LIVE **INSIDE** THE PRINTER'S FILTERING AND ROUTING · 2026-09-01 19:0x
**Topic:** BACKEND · **Progress:** 0/1 · not started

> *"the templates also need to be within the printer filtering and routing correctly and
> discarding"*

The templates are not a separate pass bolted beside the printer — they are the mechanism the
printer filters, routes and discards WITH. If a template can be removed without the routing
changing, it is not wired in.

## A9 · THE 10-15% LAW — THE ENGINE THROWS THE GARBAGE OUT BY DEFAULT · 2026-09-01 19:0x
**Topic:** BACKEND · **Progress:** MEASURED 2026-09-03 · **folded into the PRINTER ZONE** with A4·A7·A8·A15 (his call: *"i want this related to the 3/4D printer it should be in the same zone. that unified printer needs to be built"*). Not a separate build — it is the printer's own acceptance test.

### THE NUMBER, TAKEN 2026-09-03 — and it does not say what it looks like it says

Source: `tv/retro_triage.json`, **437 reels, all fully triaged** (`full=437, partial=0`), 15,947 frames.

| reading | measured | vs the 10-15% band |
| --- | --- | --- |
| frames that carried data | **1,029 / 15,947 = 6.45%** | **BELOW** |
| reels worth saving | **33 / 437 = 7.55%** | **BELOW** |
| **frames kept, counting only the 33 reels that HAVE panels** | **1,029 / 5,489 = 18.75%** | **ABOVE** |

**⚠ THE AGGREGATE IS A STATEMENT ABOUT WHAT HE FILMED, NOT ABOUT THE FILTER.** 404 of 437 reels contain
ZERO panels and they hold **65.6% of every frame** — those are gameplay reels, not stash reels, and no
filter quality can move that number. Read against reels that actually contain panels, the pipeline sits
at **18.75%**, just above his band, not below it. The two readings differ by 3x and both are honest;
which one is the law is a decision, not a measurement.

**⚠ A CHECK I RAN ON MY OWN INSTRUMENT, because a 3x spread invites a wrong story.** Per-reel keep-rates
run from 0.8% to 100%, and my first bucketing printed a `100-109%` row that looked like panels exceeding
frames — an impossible reading that would have meant the units were incommensurable. It was **my bucket
label**, not the data: `int(100.0//10)*10` lands in a bucket named for 100-109. Verified directly —
**zero reels have panels > frames**, and `sum(panels) == sum(kinds) == 1029` exactly. The units are
commensurable and 6.45% stands. [[feedback-suspect-the-instrument]]

**WHAT THIS DECIDES ABOUT THE PRINTER CLUSTER.** The number cannot yet distinguish *"the filter is
working"* from *"404 reels genuinely had nothing"*. The test that CAN is the contradiction A4 was born
from — reels claiming "examined, nothing to take" that a survey says held panels. **That is the first
thing to build in the printer zone**, because it is the acceptance test the whole cluster is graded by.
Until it exists, the 10-15% law is a badge; after it, it is a gate.

_(previously: in progress · the 10-15% law)_

> *"withing the 100% reels only 10-15% are worth saving.. the rest should by default within the
> processing engines automaticaly filter the garbage out and leave the information reels with data
> to extract from and then there another layer"*

**A measurable law, and it doubles as the gate.** Of 100% of reels, 10-15% carry data worth
keeping. The engines must reach that ratio BY DEFAULT, automatically, with no human deciding — and
then a further layer works only the survivors. ⚠ If the pipeline is keeping far more than 15%, the
filter is not working; if far less, it is eating data. Either way the number is the alarm.

## A10 · THE FISH DOWN THE STREAM — PROBE ONE REEL THROUGH THE WHOLE RIVER · 2026-09-01 19:0x
**Topic:** BACKEND · **Progress:** ✅ SHIPPED v2505 · `tv/reel_river.py` walks every reel and names the DECIDER and the QUESTION for each stage. Measured: 40 reels, 28 swept, 12 releasable, frame door no on 15 / UNASKED on 25, **0 gaps**. ⚠ THE FINDING: 12 RELEASABLE beside a frame authority refusing every seal is NOT a contradiction — v2314 ruled two granularities correct and withdrew the collapse — and nothing on any screen said so, which is the gap A10 actually names. A gap is two deciders answering the SAME question differently

> *"remembe the fish needs to go down the stream.. probe it down the stream meaning the reel needs
> to go do the river stream an see that its properly syncned and no gaps... and everything is
> working and collaborating.. and all is working an nothing is stale"*

An END-TO-END probe, not a unit test of each stage. Put one reel in at the top and follow it all
the way down: every stage it touches, in order, asserting at each step that it is synced, that
there is no gap, that the stage actually collaborated with the next one, and that nothing it read
was stale. **This is the only check that can catch two stages that each work and never meet**
([[the-unjoined-end]]). Wire the result to the heart.

## A11 · ARE ALL THE LANES EVEN HERE? — INVENTORY, THEN PROVE EACH ONE · 2026-09-01 19:0x
**Topic:** ARCHITECTURE · **Progress:** measured · the census counts 21 vessels: 11 WATCHED, 8 DARK, 2 UNKNOWN. Proving each one is unstarted

> *"im not sure all the lanes are here.. working and reverse engineeered"*

An honest census of every lane in the console: does it exist, does it run, does it collaborate with
its neighbours, and has it been reverse-engineered. ⚠ Precedent: THE HEART can only supervise what
reports in one vocabulary and what it knows exists — ⚠ **28 thread targets, 11 supervised, SEVEN
persistent loops unwatched** (`tv/lane_census.py`, the `lane-census` gate, 2026-09-01). The
earlier figure here was **21 starts / 11 registered**, from an ad-hoc classifier that was wrong
twice in the same way; the census carries its own `--prove`. Grok Bot flagged this line as stale
(GB-B-6) while the gate at the same SHA already said 28/11/7 — a next model restoring this task
from TASKS.md would have briefed the wrong number. A lane
nobody registered is a lane nobody watches. Output is a table with UNKNOWN as a legal answer.

## A12 · BLUEPRINTS AND REVERSE BLUEPRINTS · 2026-09-01 19:0x
**Topic:** ARCHITECTURE · **Progress:** proven · blueprints regenerate and agree (19·19)

> *"blueprints.. reverse blueprints.. everything"*

Both directions, and they must AGREE. Forward: what the system is supposed to do. Reverse: what the
code actually does, derived from the code. Where they disagree, THAT is the finding — the same
two-way-agreement principle as A5, applied to the whole console rather than to one fact.


## A13 · THE VISUAL HARNESS MUST FEED THE GATE · 2026-09-01 19:1x
**Topic:** GATES · **Progress:** ✅ **SHIPPED v2511** — the render gate feeds the ratchet since v2475, and the visual harness now feeds the gate too (`tv/eye_vs_beat.py`, registered). ⚠ THE JOIN WAS IMPOSSIBLE BEFORE: the console publishes a beat and stores NO HISTORY, so an observation and the beat to check it against could never be reconciled afterwards — which is exactly why the 2026-09-01 blank-white catch reached nothing. `observed()` captures the beat AT THE MOMENT OF LOOKING now. ⚠ It only works FORWARD: the 13 existing rows report NO-BEAT-CAPTURED, never 'no contradiction'. ⚠⚠ And the check was WRONG ON ITS OWN CASE — written against the FLAT fixture beats while the live `panels_of()` returns them NESTED, so against his running console it reported AGREES while the beat claimed a panel shown at h=1309

> *"i want this part of the workflow.. what about the visual harness with grok bot where is that?"*

✅ **IT NOW REACHES A GATE** (v2404, `tv/human_eyes_gate.py`, registered as `human-eyes`;
hardened v2405 after a cold cross-family read found its exit code was decided by string-matching
its own output, and that a brief timestamped ahead of `now` read as fresh). ⚠ This line said
**IT EXISTS AND IT REACHES NOTHING** for a whole ship after the reaching landed — Grok Bot caught
it (GB-B-7). The half still NOT built is the live-console contradiction check, filed rather than
faked. Originally: `tv/ask_view.py`, `tv/human_eyes_ledger.py`, the
`human-eyes-harness` skill and briefs HE-1…HE-5 (gh #181-#186) are all built. The ledger has 8 rows
and one of them is a real catch: on 2026-09-01 at 16:21:45, verdict **LOOKED**, the eye reported his
webview blank white while the beat published `taskforce shown H=502 top=1050` in a **660px** window.
That finding sat in an untracked `tv/.human_eyes.jsonl` and reached no gate, no blocker and no
version. **An observation that reaches nothing is a diagnosis nobody made.**

What it needs:
- an observation with verdict `LOOKED` that CONTRADICTS the console's own beat raises a **blocker**,
  the same way `render-gate-vision` does — not a note in a file
- the workflow reads the human-eyes ledger as a gate input
- ⚠ and it is currently half-crippled by two things outside the code: pointer injection is dead
  without macOS Accessibility (HE-1, HE-4), and the Grok CLI is `402 Payment Required` so the CLI
  seat returns EMPTY. An empty seat is never agreement. MCP is the working transport today.

Live consequence already filed as gh #200.


## A14 · THE CHRONICLE COUNTER ONLY GOES UP, AND THE LEDGER IS THE PROOF · 2026-09-01 19:2x
**Topic:** BACKEND · **Progress:** ✅ **1/1 SHIPPED v2509** (`tv/ledger_highwater.py`) — **the MONOTONIC COUNTER only** (his call, 2026-09-03: *"do whats recomendeed"*). Requirement 1 is cheap and carries almost all the safety: a chronicle count may rise and may never fall, and a drop is raised as a DEFECT rather than rendered. ⏸ **Requirements 2-4 — every ledger entry carrying its own re-verifiable proof — are DEFERRED**, being a retrofit across the whole ledger. **CONSEQUENCE ACCEPTED:** a drop is still caught the moment it happens; what is given up is re-proving one specific OLD entry later

> *"i want to see ledgers proof and a counter for chronicles only going up never down they can
> always verify proof with the ledger that way profile and data cant ever be lost!"*

**FOUR REQUIREMENTS, AND THEY ARE ONE MECHANISM.**

**1. THE COUNTER IS MONOTONIC.** A chronicle count may rise and may never fall. A drop is not a new
truth — it is a DEFECT, and it must be raised as one rather than rendered. Same law as task 166,
scoped to the chronicles.

**2. EVERY LEDGER ENTRY CARRIES ITS PROOF.** Not a display string. A reel, a frame, a witness
count, a session — enough that the entry can be re-verified later by something that was not there
when it was written. ⚠ MEASURED BLOCKER, and it is the same one blocking 166: `d2r_foundLog` is
**412 rows shaped `{name: "Jun 22, 2026 · 02:00"}`** — a date rendered for a human, with no reel, no
frame, no witness. **8 of his 169 owned items have no log row at all.** Today the ledger cannot
prove anything, so the counter has nothing to check itself against.

**3. THE COUNTER AND THE LEDGER MUST BE RECONCILABLE, ALWAYS.** The count is not a stored number to
be trusted — it is a claim that can be re-derived from the ledger on demand and compared. When they
disagree, THE DISAGREEMENT IS THE FINDING: publish both, never average, never prefer the newer.

**4. THEREFORE THE PROFILE CAN NEVER BE LOST.** This is the point of the whole thing. If a profile,
a namespace or a localStorage store is wiped, drifts or forks, the ledger rebuilds it — because the
ledger holds the evidence and the evidence is enough to re-derive the state.

### Why this is not theoretical — it has already happened, more than once
- **The board window was EPHEMERAL until v2043.** `webview.start()` with no `private_mode` gave a
  throwaway localStorage per launch, so writes vanished on close.
- **Three namespaces currently DISAGREE on his own machine:** `d2r_grailFarm` 389 (his) vs 102
  (bare); `d2r_rwMade` 0 vs 99. Two stores, two answers, no arbiter.
- **A book has lost rows two ways before** — a purge, and four separate programs whole-file-writing
  the same JSON and erasing each other's appends seconds later.
- **`d2r_owned` = 169 with no per-entry evidence** is task 133, which is blocked on exactly this.

### What must be built
- an append-only chronicle ledger where a row carries `{item, count_after, evidence{reel, frame,
  witness, session}, ts, actor}` — and **a human action is itself valid proof** (his ruling:
  *"anything done manually by a human is proof and witness enough and bypassed"*)
- a `verify()` that re-derives the counter from the ledger and reports AGREE / DISAGREE / UNKNOWN —
  never a silent max()
- a monotonic guard that raises a blocker on any decrease, wired to the heart
- a `rebuild_profile_from_ledger()` path, and a test that PROVES it: wipe a fixture store, rebuild
  it, assert byte-equality. ⚠ Fixture only — never his live store.

Closes the hole under tasks **133** and **166**.


## A15 · THE RIVER — ONE START POINT, ONE FUNNEL, THEN PER-REEL ROUTES · 2026-09-01 19:3x
**Topic:** BACKEND · **Progress:** 0/1 · not started — THE RIVER

> *"the same feeding system and same routing system working and funneling starting from the same
> start point and slowly down the river changing routes individually and acocridngly relvant to
> that speicfic routed reel... depending on what inititially has been processed through out 3d
> printer that filters properly it all unified... every single reel goes thourh the printer and
> comes out clean on the other end accoinrdlgy relevant to that specific reel needed to be
> extracted from indiviudally acoidnly to the scenario"*

**THE ROUTING LAW, and it resolves the apparent contradiction between A7 and "every reel is
different".** They are not in tension:

- **ONE START POINT.** Every reel enters at the same place. No lane has its own front door.
- **ONE FUNNEL.** They all flow down the same river together, through the same feeding and routing
  system, for as long as they are indistinguishable.
- **THE PRINTER DECIDES WHERE THEY DIVERGE.** What the 3D printer FINDS in a reel is what selects
  its route — the route is *derived from the content*, never declared up front, never guessed from
  a filename or a focus stamp. ⚠ Precedent: v1783 — *a default is not a declaration*; trusting an
  untouched "stash" stamp labelled town, a fight and a Chronicle page as stash panels.
- **THEN THE ROUTES SEPARATE, PER REEL, BY SCENARIO.** Each reel takes the path its own content
  earns, and gets extracted from according to what it actually holds.
- **AND EVERY ONE COMES OUT CLEAN AT THE FAR END.** "Clean" is a state the pipeline must be able to
  ASSERT per reel, not a hope. A reel that cannot be shown clean is not finished.

**This binds A4 (the printer), A7 (one unified logic), A8 (templates inside the routing) and A10
(the fish down the stream) into one system.** A10 is how you prove A15 works: put a reel in at the
start point and watch it take its own route the whole way down without a gap.

⚠ **AND IT GATES THE PRUNE.** See task 146 — his approval of the 4.34 GB release is explicitly
conditional on this being built and running first.


## A16 · THE HEART OF THE CONSOLE — AND WILSON SCORE IT ALL · 2026-09-01 19:4x
**Topic:** ARCHITECTURE · **Progress:** shipped as the heart · v2443-v2446; Wilson scoring extended to routes in v2487

> *"make sure watchdog and corrobator eagle eye and doctor (the Heart of the Console) is what we
> called it and wilson score it all!! connect it all to the HEART OF THE CONSOLE"*

**THE HEART IS FOUR ORGANS AS ONE LAYER — his name for it, and the name is the spec:**

| organ | what it does |
|---|---|
| **EAGLE EYE** | sees everything — the surface that shows the whole console's state at once |
| **WATCHDOG** | notices when something stops, drifts or lies, and acts |
| **CORROBORATOR** | requires two independent witnesses to agree before a fact is trusted |
| **DOCTOR** | probes a lane on demand and reports MISSING vs BROKEN vs HEALTHY |

**"Connect it to the heart" means MAKE IT SUPERVISED, not merely built.** A lane that works and is
unwatched is not finished. This is the umbrella over A1 (self-proving gaps), A2 (Wilson), A3 (the
capability matrix), A11 (the lane census) and A13 (the harness feeding the gate) — all five are the
heart reaching further.

### ⚠ TWO MEASURED LIMITS THAT MUST BE FIXED FIRST, OR THE HEART SUPERVISES AIR

1. **IT CAN ONLY SUPERVISE WHAT REPORTS IN ONE VOCABULARY.** Four organs speaking four dialects is
   four dashboards, not a heart. One status vocabulary, one shape, every lane.
2. **IT CAN ONLY SUPERVISE WHAT IT KNOWS EXISTS — and it does not know.** Measured by the
   `lane-census` gate: **28 thread targets, 11 supervised, SEVEN persistent loops unwatched.**
   (The **21 / 11** that stood here was from a classifier later proven wrong; do not quote it.)
   Seven live loops run unwatched, and the heart reports green over them
   because absence and health look identical. That is A11, and it is a PREREQUISITE, not a sibling.

### WILSON SCORE IT ALL
> *"wilson score it all!!"*

Every fact the heart holds carries a confidence, not a boolean — so "we are sure" and "we saw it
once" stop rendering the same. ⚠ And per A2 this is NOT satisfied by adding the score in more
places: today Wilson is *a second spelling of the same rule*, because the floor makes confidence and
confluence irrelevant. Make the score take **confidence and confluence** into account, then wire it
through the heart: 1/1 → 0.207 · 3/3 → 0.438 · 6/6 → 0.610 · 12/12 → 0.757.

**AND THE HEART MUST BE ABLE TO SAY UNKNOWN.** A green lamp over a lane nobody measured is the
failure this whole layer exists to prevent. [[unknown-stays-unknown]]


## A17 · THE TV·D CONSOLE NEEDS AN EDITORIAL REDESIGN · 2026-09-01 20:0x
**Topic:** VISUAL · **Progress:** in progress · typography, type scale and the hero/dash split landed across v2147-v2181; the editorial redesign continues

> *"i want this visually structured alot better. flagship style.. i want titles for whats needed
> editorial style.. this looks messy and complicated. i want it unerstanding and typography and
> clear and symmetric OCD alligned"*

Sent with a full-window screenshot of the TV·D tab at v2399. **Two independent eyes read it — mine
and Grok's (cross-family, MCP transport) — and the findings below are only the ones BOTH could see
or that I verified in the pixels myself.** Grok's two overstatements are recorded at the bottom so
nobody rebuilds on them.

### CONFIRMED DEFECTS
1. **TRUNCATION IS EVERYWHERE IN THE STAT ROW.** Five cards, four of them cut:
   `Session 22…` · `Session 13…` · `5 chronicle…` · `528 runs lo…` — and `leave the reel · bac…`
   on CLOSE THEATRE. **A stat card whose stat is ellipsised has failed at its one job.**
2. **THE FLEET ROWS BREAK.** `Wife offline · v2101 · 298 behind` then **`PC`** orphaned onto the
   next line. Three-machine rows on an unforgiving grid.
3. **LABELS AND VALUES ARE THE SAME SIZE AND WEIGHT** in several places, so nothing separates a
   name from a number. There is no type SCALE — there are sizes.
4. **RAW MACHINE OUTPUT ON A HUMAN SURFACE.** `1% 3002.9MB zero-pages 1787523300658_1` ×5. Epoch
   ids and internal lane names rendered for a person. [[label-outlived-referent]]
5. **THE FUNNEL READS AS BROKEN, AND IT IS NOT.** Six stages, and four show a dim `0` —
   `1 FILMED 0 · 2 TRIAGED 0 · 4 BANKED 0 · 5 VAULT DONE 0` against `3 SWEPT 28` and
   `6 RELEASABLE 12`. **An empty stage and a broken stage look identical.** Nothing says whether a
   zero is "nothing was owed" or "nothing ran". [[unknown-stays-unknown]]
6. **NO EDITORIAL TITLES.** He asked for these by name. Sections begin with data, not with a line
   that says what the section is FOR. `MOST FILM FOR LEAST SIGNAL` is the only real one and it is
   set as a wall of caps, mid-paragraph.
7. **A CONTROL WHOSE LABEL DOES NOT KNOW WHAT IT DOES** — `ready?` beside a white blob, in a 3×3
   RARE PATHS grid whose buttons are three different widths. Symmetry was asked for by name.
8. **NO FOCAL PATH.** The eye lands on `28` and `12`, then everything competes equally — sidebar,
   file list, transport strip. Nothing is first.
9. **THE HEADING IS CUT OFF AT THE TOP** — the line above `894 panels / 5022 frames · 40 reels
   surveyed` is clipped by the scroll container.

### WHAT HE ASKED FOR, AS ACCEPTANCE CRITERIA
- **Flagship, editorial.** Every section opens with a TITLE that says what it is for, in a voice
  written for him, not for the engine.
- **A real type scale** — display / section / label / value / meta, each doing one job, so a label
  can never be mistaken for a value.
- **Symmetric, OCD-aligned.** One grid. Equal gutters. Buttons in a row share a width. Numbers on
  one baseline, `tabular-nums` wherever digits stack.
- **Nothing ellipsised.** If it does not fit, the card is wrong — not the sentence.
- **A zero must say WHICH zero it is.** Measured-and-empty vs never-ran are different facts.

⚠ **VERIFY IT THE WAY HE ASKED:** render at his width AND at 1440/1120/901/375, LOOK at the PNG,
then hand it COLD to the cross-family eye — *no premise about the subject*, ask what it DEPICTS,
and crop to the region, because a full-page "clean" from that eye has been a FALSE CLEAN three
times measured. Human side of the harness closes it. [[visual-regression-detector]]

### GROK'S TWO OVERSTATEMENTS — recorded so nobody rebuilds on them
- It said the RARE PATHS buttons have no text labels. **They do** — dark · seal · bridge · relaunch
  · eagle · ready? · gate · repair · ledger. The real defect there is inconsistent WIDTHS and one
  unclear label, not missing ones.
- It said the file-list names wrap or cut mid-character. **They do not.** The columns align; the
  defect is that the content is machine ids at all.

---

## 🔥 THE URGENT THREE — "task these in first urgently before the other tasks"

| # | What | State |
|---|---|---|
| **165** | **THE NEXT LOOK** — the harness has EYES AND NO HANDS. Synthetic pointer events need macOS Accessibility; without it `CGEventPost` silently succeeds and moves nothing. So Claude names the pane in CODE and a human eye photographs it. `tv/ask_view.py vault --brief HE-2` → `.view_request.json` → `view_request()` publishes 5 states on `/api/status` → the console honors it ONCE, stamps the screen, puts his tab back. Refused states (STALE/UNKNOWN/HELD/BROKEN) paint **nothing** on his screen. Contract = `gh #186`. | **SHIPPED v2399** |
| **166** | **LOCK THE NAMESPACE, and the ledger is authoritative.** His ruling: *"NO i want it locked to whats it is now"* / *"not only up — its also in the ledger with proof, that way from there it can reupdate its profile if needed"* / *"anything done manually by a human is proof and witness enough and bypassed."* PIN `I·77f64154·`, profile `main`. The law is **MONOTONIC** (may rise, never fall), not equality. | **BLOCKED — measured.** The loggers do not carry proof today: `d2r_foundLog` is 412 rows of `{name: "Jun 22, 2026 · 02:00"}`, a display string with no reel/frame/witness, and 8 of his 169 owned items have no log row at all. The rebuild he wants is right; the data cannot do it yet. |
| **167** | Show the eye in **THE FLEET** when it is live. | READY (after 165 lands) |

---

## ✅ READY TO APPLY — one, and four that quietly landed

⚠ **v2435 — FOUR OF THE FIVE ROWS BELOW SHIPPED IN v2400 AND SAT HERE FOR THIRTY-FOUR VERSIONS.**
Grok Bot filed it as **GB-B-3 / GB-B-4** on 2026-09-01 and repeated it on nineteen consecutive
watch ticks; it was right every time. A list that names finished work as READY costs someone the
work twice, and it is why `tv/tasks_freshness.py` now exists — a row carries a FINGERPRINT (the
string whose PRESENCE means the work is undone) and the gate refuses when one disappears.

⚠ AND THE RE-MEASUREMENT ALMOST GOT **159** WRONG IN THE OTHER DIRECTION. Grepping the doc for the
old wording still returns a hit — inside the note recording the fix (*"This page said 'KEEP = 2
distinct sessions...' until this"*). My own prose about a fix satisfying my own search for the bug.
Closed on what the page ASSERTS today (line 70: *"THREE LOOKS TO KEEP, FOUR RECORDINGS TO THROW"*),
never on a grep count.

| # | What | Where | Fingerprint |
|---|---|---|---|
| **135** | Daily-pick dead branch. 3 edits + 1 spec test. ⚠ Three namespaces use `'grail'`; **only the chron-entry key may change.** | `bible.html` | ⚪ **none** — the undone-ness has no single string, so `tasks_freshness` reports it UNKNOWN every run rather than passing it silently. |

### Landed in v2400, verified by measurement 2026-09-02

| # | What | The measurement that closed it |
|---|---|---|
| **143** | Delete `fv.onclick`, extend the panel's FLEET section. | `grep -c 'fv\.onclick' bible.html` → **0** |
| **159** | Doc said KEEP=2 / THROW=3; code ships 3 / 4. Same as **GB-B-1**. | `PROJECT_VAULT_MANAGER.md:70` now asserts *"THREE LOOKS TO KEEP, FOUR RECORDINGS TO THROW"*; `vault_retro.py:163,165` ship `KEEP_MIN_WITNESSES = 3` / `THROWOUT_MIN_WITNESSES = 4`. v2400's own message: *"Closes Grok's GB-B-1."* |
| **153** | Register `hover_wilson` as a gate — fail on LEAKS, never on UNPROVEN. | **5** references in `tv/run_gates.py`; v2400 pinned its predicate in both directions. |
| **164** | Paint-witness invariant: `>=`, not `==`. | `control_app.py:11592` — `elsHigh >= _UI_PAINT_FLOOR_ELS` |

---

## ⛔ BLOCKED / HIS CALL — six

| # | What | Why it is not mine |
|---|---|---|
| **133** | No per-entry evidence in `d2r_owned`. | Answered by **166**'s ledger ruling — do 166 first. |
| **146** | 4.34 GB / 4,128 frames releasable, keeping all 894 that carry. | **The apply is his.** He ruled "yes" on the principle: a frame the printer examined and found empty may be deleted. |
| **155** | Would spend paid reads. | His money. |
| **154** | Blocked by 155. ⚠ **My own framing was RETRACTED:** `pruned_mb=0` and `hist_bytes=None` are HARDCODED at the only call site, so `prunedMb: 0` across 7,009 rows is a fact about the CALLER. "The prune has never freed a byte" is **not supported**. The real defect is that the field can never report anything. | `tv/control_app.py:14920` (writer at `:11954`) |
| **136** | Blocked by vault names. | |
| **148** | Blocked by vault names. | |

---

## 👁 OPEN BRIEFS — human eyes, four

| # | Brief | Needs | State |
|---|---|---|---|
| **182** | **HE-2** — what number does the VAULT pane actually display? Three sources disagree: `/api/vault_ledger` = **7**, `status.ledgerBackup.counts.owned` = **169**, what he expects = **~40-46**. | console only | **OPEN, GO given** |
| **185** | **HE-5** — is the footer hover ONE line, with everything moved into the click window? Ships in v2397. | console only | **OPEN** |
| **181** | **HE-1** — does the hovered cell's tooltip name the item actually in that cell? | game + **HID** | **BLOCKED** — pointer injection is dead in this build; Accessibility is not granted. Do not fake it and do not ask him to pose a hover. |
| **184** | **HE-4** — overnight from 03:00, autonomous: 30+ slot hover calibration, enough n for Wilson. | game + **HID** | **BLOCKED** — same. This was the run that would have turned `anchor` from UNPROVEN into scored. |

---

## 🤖 GROK HANDOFF QUEUE — `gh #179` (backend) · `gh #180` (live)

Grok Bot reads, disagrees, and queues. It does not edit. Claude owns the fix and the ship.

| ID | Claim | State |
|---|---|---|
| **GB-B-1** | `PROJECT_VAULT_MANAGER.md` said KEEP=2 / THROW=3; the code ships 3 and 4. | **CLOSED v2400** — the page now asserts *"THREE LOOKS TO KEEP, FOUR RECORDINGS TO THROW"* (line 70). Re-verified 2026-09-02. ⚠ Grepping for the OLD wording still hits, inside the note recording the fix — read the assertion, not the grep. |
| **GB-B-2** | HOLDS *writers* are gated, but ~289 possession claims already sitting in `d2r_owned` are undone by no gate. | **ANSWERED** — 289 = owned 169 + setPieces 120, which is arithmetic and not a leak. ⚠ `d2r_owned` is TESTIMONY; only he may overrule his own ticks, so there is no cleanup for me to do here. |
| **GB-L-1** | HE-1 look — hovered cell matches tooltip item + true slot. | **UNKNOWN** 2026-09-01 — no `D2R.exe` on konyo-3. Re-run when the stash is open. |
| **gh #186** | The eye's half of task 165 — the contract for what Claude may ask an eye to photograph. | **OPEN** |

---

## CF — THE CONSOLE'S OWN SEVEN (2026-09-01, from THE STATE OF THIS CONSOLE)

He photographed the state panel and said *"task these in too.. im not sure your aware of them"*.
I was not. These are the console reporting on itself, unprompted — the Heart working — and nothing
was reading it. Two more (CF-6, CF-9) were found while grounding the first seven.

- ◻ **CF-1 EXTRACTION LANES** — chronicle 4.8h and vault 7.9h since last work. ⚠ idle-with-owed-0
  is a lane WORKING; the job is to report `owed` beside `lastWorkTs`, not to restart anything.
- ◻ **CF-2 BOARD JOIN** — registering targets the CONSOLE window (`path=/`, no `chronicleApply`),
  not the board. Same root as CF-8.
- ◻ **CF-3 ENGINES CORROBORATE** — `eagle-ran-every-check` 32 rows vs 34 roster checks. ⚠ name the
  two missing checks; a delta of 2 is not actionable, two names are. Suspect the instrument first.
- ◻ **CF-4 CONSOLE UI FAULTS** — 3 self-heals in 24h; page beating while blank (11,817 elements vs
  a high-water 84,541). ⚠ the self-heal converts a reproducible bug into an intermittent one —
  capture the pre-rescue state BEFORE healing.
- ◻ **CF-5 PROGRESS NUMBER** — two worlds claim him: `77f64154` 290 uniques vs `c5c2c92d` 280,
  4.6 days apart, both sets=120. ⚠ HIS TICKS ARE TESTIMONY — do not resolve in code by preferring
  the newer; that is already the behaviour being warned about. Route to truth is a GB-L brief.
- ◻ **CF-6 GUEST-WORLD GROWTH** — `board_tally.json` holds ~150 routes and **exactly 2 have
  non-zero counts**; ~148 are probe artifacts, one per CDP look, unbounded and unpruned. Same
  mechanism that took `~/.grok/sessions` to 11 GB. Stop recording at the door, don't prune later.
- ◻ **CF-7 FOOTAGE HAS A REEL** — 1 frame outside every reel. Small in bytes; the point is that a
  frame CAN exist outside the structure that governs frames. `tv/orphan_fold.py` has the plan.
- ◻ **CF-8 BOARD IS CLAIMED = UNKNOWN** — correct as written, do NOT turn it into a number. Worth
  doing: surface the 110-of-110 same-world agreement as EVIDENCE for CF-5, and carry the last
  known answer WITH ITS AGE instead of a bare UNKNOWN.
- ✅ **CF-9 THE GATE'S VIEWPORTS** — render_check rendered four heights, all taller than his
  660px window. Fixed v2406 (his real 1120x628 + a pre-scroll reachability probe). ⚠ STILL OPEN:
  the fixture lays out differently from the live app (taskforce y=224/h=30 in the gate vs
  y=1050/h=502 live), so that gate cannot cover layout-in-situ and must not claim to.
