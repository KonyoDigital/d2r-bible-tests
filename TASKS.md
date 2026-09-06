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

## ⚠⚠ DRIFT AUDIT — 2026-09-05, and the file's own failure recurred

He asked for the list *"optimised to perfection so theres nothing there"*. A read-only pass over all
1,215 lines, cross-checked against 400 commits, measured this:

> ⚠⚠ **RE-AUDITED 2026-09-05 BY A READ-ONLY FLEET, AND THIS AUDIT BLOCK HAD BECOME THE MOST STALE
> TEXT IN THE FILE IT AUDITS.** Every headline figure below was wrong when re-derived. That is not
> irony for its own sake — **a drift audit that itself drifts is worse than none**, because it is
> the section everyone reads first and trusts most. Measured, and each one is a one-line command:
>
> | it said | re-derived 2026-09-05 | how |
> |---|---|---|
> | 1,215 lines | **1,986** | `wc -l TASKS.md` |
> | HEAD v2657, 9 ships absent | **v2681** | `tv/WINDOWS_SHIP.json` |
> | 142 gates | **143** | `grep -c '^    Gate(' tv/run_gates.py` |
> | CF-1 twins "116 lines apart" | **1,095** (L128 vs L1223) | both lines still live |
> | §8's "30-gate set" | ~~143~~ → **146** — ~4.9x stale | same grep |
>
> ⚠ **AND THE A2 LOCK PROSE BELOW IS FALSE AGAINST THE LIVE MODULE.** `python3 tv/self_arming.py`
> returns **12 of 17 OPEN, 0 HARDENED**, with `prune.arm`, `vault.apply` and `vault.sweep_start`
> all **LOCKED**. So the LOCKED *table* in this file is right and the OPEN *prose* (L105, L443,
> L626-628, L681 — "prune.arm opened itself", "14 of 15 locks are OPEN", "A2 IS DONE / 4-of-4") is
> stale. Where a table and a paragraph disagree here, **run the module**; do not average them.
> [[unknown-stays-unknown]] [[inherited-claim-is-not-evidence]]

| fact | measurement (⚠ as first written — see the re-audit above) |
|---|---|
| newest LANDED row in this file | ~~v2648~~ → ~~v2681~~ → **v2690** (`4254d925`). ⚠ THE TABLE BELOW NOW LISTS v2691 AND v2692 TOO, AND THEY HAVE NOT LANDED — they are committed and held while he is gaming, because the pre-push gate runs Playwright and a full render sweep on his Mac. A row in a LANDED table that has not landed is the same defect this audit exists to catch, so it is said here rather than left to be discovered |
| HEAD | ~~v2657~~ → ~~v2681~~ → **v2692** (`1d1a6385`, 12 commits unpushed while he was gaming) |
| "the 30-gate set" (§8 and elsewhere) | `grep -c '^    Gate(' tv/run_gates.py` = ~~142~~ → **146** (2026-09-06). The number 30 is now **~4.9× stale**, and the drift outran its own audit inside six days — which is the point the audit was making |
| rows claiming a state that is no longer true | **11** as first written · **+2 found 2026-09-06** (`sunder6` and `sunder3forms` both said "FIXED AND VERIFIED v2680" with real measurements attached; v2680 was REVERTED in v2685 and the fix rode out with it, leaving the claim standing). ⚠ A revert undoes code and cannot undo a claim written on a list, and nothing re-checks a row when the version it names is reverted |
| ids carrying work that is really ONE item | **8 clusters** — the largest is **7 ids for one decision** |
| rows shown as owed by him that he has ALREADY ruled on | **6** |

⚠⚠ **AND THE GATE BUILT TO PREVENT EXACTLY THIS WAS WATCHING ONE ROW.**
`tv/tasks_freshness.py` graded only the heading `"READY TO APPLY"` — a table that had drifted down
to a **single entry (#135) whose own cell reads `✅ SHIPPED v2474`.** So the freshness gate was
grading one finished row and reporting UNKNOWN on it, every run, for ever, while every other table
drifted unwatched. **A gate whose subject moved out from under it is the same defect as a gate that
never runs.** Widened in v2658 to `READY TO APPLY · URGENT THREE · BLOCKED / HIS CALL · OPEN
BRIEFS` — 1 graded row became **14**. [[the-unjoined-end]] [[regression-guard]]

⚠ **THE SHARPEST INSTANCE, because it needs no judgement:** row **155** read *"BLOCKED — his
money"* while the ruling unblocking it is written **73 lines above it in this same file**. And
**CF-1** appears twice in two contradictory states — ~~116~~ **1,095 lines apart** (L128 says
*"CLOSED, and the premise was FALSE"*; L1223 still reads as live work). Even the distance in this
sentence had drifted, by a factor of nine. A file long enough to contradict itself is a file nobody
can read to the end.

**The deduplicated remaining set is at the bottom of this file, under
§🎯 THE TRUE REMAINING SET.** Read that, not the historical tables above it.

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
| **v2646** | **THE TESTED ENCODER IS NOT THE USED ENCODER.** `fleet_mask.encode` is round-trip tested against `fleet_mask.decode` and has **zero production callers** — AST-measured, and it is four unreached functions not one. Every mask that has ever gone on the wire is produced by an **inline JS snippet** built as a string inside `control_app.board_mask()` and run via `_ejs`. The suite proved a pair that never runs together in production while the code that does run had no test at all. The shipped snippet is now lifted **by AST** and compared byte-for-byte against Python; RED-proven by flipping it to MSB-first. ⚠ I briefly declared the row's explanation refuted after grepping `bible.html` (6.2 MB, zero hits) — it was right, the JS is embedded in PYTHON. **An absence found by searching the wrong artifact is not an absence.** · on origin `33c69a1f` |
| **v2647** | **THE SABOTAGE THAT COULD NOT FAIL — REG-600, both instances.** `prune.reports` banked 24/24 by handing `disk_history_append(pruned_mb=None)` and asserting the row came back `None`, against a writer that was a **pure passthrough with no validation in it**. `reel.route` had two such axes of seven: one compared **two module constants** eight times, one graded an observation while its own comment said *"the caller must refuse it"* — and never called it. The fix is a real refusal **at the WRITE end** (`credible_pruned_mb`); the screening used to sit at READ time, so impossible claims reached his durable series and were filtered afterwards by one reader. ⚠⚠ The replacement axis found a real defect on its first run: `_station_of(None)` returns UNKNOWN **by design** and its only caller raised `AttributeError` before it could. ⚠⚠ And the retired evidence was **still being counted** — `_fold` keys on `ref`, so the new axes superseded nothing and the lock read **n=56, 32 real refusals plus the 24 identity assertions the rewrite existed to remove**. `withdraw()` supersedes an axis with an `n=0/k=0` row and a required reason; nothing is deleted. · on origin `32274b28` |
| **v2648** | **THREE HOLES A COLD EYE FOUND, AND ALL THREE WERE MINE.** `credible_pruned_mb` handed to a **different model family COLD**. It landed 3 of 5: **negative zero** (`-0.0 < 0` is False in Python, so the row published `prunedMb: -0.0`), **0.9 MB against a 0-byte corpus**, and **2.0 MB against a 1 MiB corpus** — the last two from one mistake of mine, a flat `+1.0 MB` tolerance. **An absolute slack is largest, relatively, exactly where the corpus is smallest.** Proportional now. It **refuted two of its own proposals**. ⚠ One it landed is deliberately NOT fixed: an unbounded magnitude with no corpus is published, because any ceiling would be a constant of mine rather than a measurement — the axis **runs, misses, and is banked**, dragging `prune.reports` from an inflated 0.9358 to a measured **0.7958 over 9 distinct attacks**. `KNOWN_MISSES` pins the LAW so a NEW miss goes red without leaving a permanently-red gate. · on origin `aa57fa55` |

> ⚠⚠ **THIS TABLE IS A HIGHLIGHTS LIST, NOT A COMPLETE LOG, and saying so is the point.** It ran
> from v2439 straight to v2646 — **138 versions** with no row, while `origin/main` moved the whole
> way. Those ships are real and their reasons are in their commit messages and on the live board;
> what is missing is this file's summary of them. **They are NOT back-filled**, because writing 138
> rows from commit subjects would manufacture a record nobody actually wrote at the time — the same
> refusal gh #210 makes about the reels that predate any door stamp. The gap is named instead.
> [[unknown-stays-unknown]]

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

- **📐 A BOUNDARY IS NEVER SETTLED BY LOOKING — BY EITHER OF US.** Five boundary claims from
  pictures were checked on 2026-09-04 and **four were wrong, in both directions.** Mine: an
  OCCLUDED line I called clipped (it was scrollable, 22px of slack), and a WRAPPED heading I called
  cut (`WHAT WATCHES WHILE YOU PLAY`, second line below the fold). The cold reader's: the crest
  called fine (it is Chrome's broken-image placeholder), the roman numeral `Ⅰ` called an overlap
  (U+2160, sitting at left 12), and the FORGE QUESTS left edge called cut (measured flush —
  textLeft 34, parentLeft 34, hiddenLeft false). **The only one that survived measurement was the
  crest, where I was right and it was wrong.** Rects, hit-tests and computed styles settle a
  boundary; a picture only says where to point them.

- **#135** — the daily-pick fingerprint. Its row says the undone-ness has no single string; I will
  not write an anchor that matches the wrong occurrence.

- ~~**THE SWALLOW CENSUS IS A VENDORED FILE.**~~ ✅ **CLOSED by his ruling, v2600** — *"remove
  kai-achilles achilles-revival surgically… if it's not needed just don't put it in."* `COPIES = ()`,
  neither sibling is named here, nothing inside either sibling repo was touched, and the emptiness
  is DECLARED (a test asserts the source says `COPIES = ()`) so an accident and a decision cannot
  look the same. The per-file map is back: a red now prints `WHERE IT ROSE` with file and delta.

- **⚠⚠ I OVERWROTE ONE OF HIS TEST SUITES AND SHIPPED IT (REG-585, restored v2604).**
  `tv/test_paint_witness.py` already existed — v2457's, 110 lines, 6 tests — and a `Write` at that
  path destroyed it in v2601, which reached origin. Found only because `run_gates` ended up with two
  gates of the same name; **a green run over a deleted test is indistinguishable from a green run.**
  Restored byte-identical, my tests moved to `test_pixel_witness.py`, both registered and green.
  **Rule: a new file is not new until the path is checked** — one `ls` would have caught it.

- ✅✅ **THE GATE SET IS GREEN EXCEPT FOR ONE, AND THAT ONE IS HIS.** Full `run_gates.py` run,
  2026-09-04 17:5x, on `085b24f5`: **`❌ 1 gate(s) FAILED: human-eyes`** — everything else green.
  That closes the arc that began with **eight** red gates nobody had seen, because
  `hooks/pre-push` runs three of thirty: REG-576 (printer_wilson + test_printer, one station),
  REG-577 (test_store_owners), REG-578 (test_import_bound_paths), REG-579 (swallow_ratchet, and
  the four sites were FIXED rather than re-baselined), REG-580 (test_heart + test_reachability).
  ⚠ **`human-eyes` is not a code defect** — it reports **3 briefs asked and never answered past
  24h: GB-L-7 55.1h · GB-L-6 67.8h · GB-L-5 68.0h** (8 recorded · 2 answered with a LOOK · 3 still
  owed). It can only ever go red on his machine, and only he can close it.
  ⚠ The run reported **exit 0 through the harness and EXIT=1 in truth** — the wrapper's trailing
  `echo`, the same shape as `git push | tail`. The `EXIT=` line in the log is what was read.

- ✅ **A11 — THE HEART'S "8 DARK" WAS REALLY 2 (REG-589 v2610, REG-590 v2611).** Every DARK row said
  the same thing; measured, **SIX of the eight ARE the supervisors** (`_bridge_prober`,
  `_console_beacon_loop`, `_console_rescue_loop`, `_mini_watchdog`, `_orphan_exit_loop`,
  `_orphan_watch`). Only `_engine_driver` and `_kai_closer_loop` are ordinary work nobody watches.
  *Nothing watches the watchman* is structural and needs a different mechanism — reported as eight
  identical gaps, six would send a reader to build the wrong thing. Then **his A1 ruling decided the
  remaining two**: `_kai_closer_loop` leaves 3,873 dated rows, so **nothing was built**;
  `_engine_driver` published a bare boolean that freezes True if the driver dies, so it got
  `engineAliveAgeMs` — a stamp, not a heartbeat.

- ~~**AT NARROW WIDTH THE MAIN COLUMN WAS UNREACHABLE (REG-588).**~~ ✅ **FIXED v2608, on origin.** At 375/640px with
  `data-state="off"`, `#home-dash` was **height 0 holding 591px** — chronicle, TZ tracker and
  missions laid out, rendered and unreachable, with `html`/`body` both `overflow:hidden` and zero
  document scroll. Cause: `minmax(0, 1fr)` — **`1fr` distributes FREE space and there was none**, so
  a starved row looked like a deliberate flex row. Fixed with a FLOOR (`minmax(45vh, 1fr)`) plus
  `overflow-y` on the stacked shell: dash **0 → 360**, and 901/1120/1440 unchanged. ⚠ Still owed:
  the dash overflows **horizontally** at 375.

- ~~**TEXT SITTING ON TEXT — a class `render_check` cannot see.**~~ ✅ **GATE BUILT (v2605-v2607) AND
  THE REAL ONES ARE FIXED (v2608).** ⚠⚠ **I published wrong numbers first**: the gate counted
  BOUNDING RECTS, and `getBoundingClientRect()` returns geometry for content an ancestor has clipped
  away. Hit-tested, the truth was **3 at 375 and ZERO at every desktop width** — against the 24 and
  2–3 I reported, including a "246×29px collision on his widest view" that **does not exist**. I had
  cropped that band, seen it read cleanly, and published anyway because the measurement agreed with
  itself across three runs. **Stable is not correct.** The class is still real and the gate stands;
  the ratchet now reads 0 everywhere.


  It measures CLIPPED / OFF-SCREEN / COVERED, none of which catches two labels drawn on top of each
  other. Measured at widths it already calls green: **375×800 has 24 overlapping pairs**, and even
  1440×1000 has 3 — one of them **246×29 px**, the EYES panel's UNKNOWN sentence on the AI READS
  bar. Shipped as a RATCHET (a rise fails, a fall fails too) because 24 today would make a pass/fail
  gate red from birth. ⚠ The counts are **debt, not a clean bill** — nobody has read the desktop
  ones — and `overlap_ratchet`'s own unit suite is OWED.

- ⚠⚠⚠ **RETRACTED (REG-594, v2615) — THE CONSOLE WAS NEVER BLANK. IT WAS BEHIND CITRIX.**
  Measured: `Citrix Viewer` 1289×752 at (108,78), layer 0, frontmost, over the console's 1120×660
  at (175,148) — **100.0% covered**. WebKit suspends painting on an occluded view by design, so
  `hidden: true`, `painting: false` and the flat white capture were all CORRECT readings of a
  healthy console. **I reported it blank repeatedly, said the cure did not cure, relaunched it, and
  called the recreate-window cure failed too — every one of those was one instrument reading a
  covered window.** ✅ The REAL defect it uncovered: `contradicts_a_hidden_beat()` treated "listed
  on screen" as "he can see it", which is why a healthy console was **reloaded 7 times in one day**
  (`rescues: 7`, `frozenBeats: 367`). Fixed, with `paint_witness` reporting OCCLUDED as a third
  state. ⚠ **The recreate-window cure named as owed to him is WITHDRAWN — there was nothing to
  cure.** ORIGINAL, kept:

- **⚠⚠ THE CONSOLE WENT BLANK WHILE REPORTING ITSELF HEALTHY, AND THE RESCUE DID NOT CURE IT.**
  Caught live 2026-09-04 by `tv/paint_witness.py` (v2601) while building it: blank white, only the
  titlebar drawn, while the page reported `blankStrikes 0` and 11,841 DOM elements. The watchdog
  FIRED correctly (`rescues: 1`) and the window stayed blank, `frozenBeats` climbing 29 → 38.
  **Detection works; the cure does not.** `rescue_worked()` now records
  `console-rescue-did-not-restore-painting` instead of counting a success — it does not retry and
  does not escalate. **OWED, AND HIS:** reloading the document is the wrong cure for a compositor
  that has stopped presenting frames; RECREATING the window is the right one, and that is a design
  decision, named rather than taken.

- **⚠ THE SWALLOW CENSUS IS A VENDORED FILE, AND IMPROVING IT NEEDS HIS CALL.** 2026-09-04: the
  per-file rank-1 map (REG-579) was written, proven, and then **reverted before it shipped** because
  `tv/swallow_census.py` has live byte-copies in `kai-achilles` and `achilles-revival`, each stamped
  with the upstream digest and guarded by `TestV2387TheVendoredCensusHasNotDRIFTED`. That guard's
  docstring carries his ruling — *"dont fix the other repo though"* and *"Do not helpfully re-vendor
  them"* — and there is no vendoring script, so syncing means hand-editing two other repos. **Owed,
  and his to decide:** re-vendor all three, or keep the census frozen and put future improvements in
  a d2r-only wrapper. ⚠ The guard's docstring is stale either way: it says the copies were "BACKED
  OUT UNTOUCHED" and both are present and committed since 2026-09-01.

- ~~**`run_gates.py` HAS EIGHT RED GATES ON `main`.**~~ ✅ **SEVEN CLOSED (v2595–v2599); the**
  **eighth is `human-eyes`, which is HIS** — 3 briefs asked and never answered past 24h. Full-set
  verdict recorded above. ORIGINAL:
  Measured 2026-09-04 by running the full gate set (30 THEN, 146 NOW — the phrase is kept as written
  because re-writing a dated measurement would falsify it), which the hook does not: it says so itself —
  *"run_gates.py runs 30 gates; this hook ran three."* RED: `printer_wilson`, `test_reachability`,
  `swallow_ratchet`, `test_heart`, `test_store_owners`, `test_printer`, `human-eyes`,
  `test_import_bound_paths`. ✅ **FIVE FIXED, NONE RE-BASELINED AWAY.** v2595 (REG-576) closed
  TWO — `printer_wilson` and `test_printer` were the SAME station and NEITHER was a leak: the
  axis pinned a field name v2572 had moved, and `shelfReach` was UNKNOWN on all 40 reels the
  whole time; under it sat a real defect, UNKNOWN with a blank reason, now joined. v2596
  (REG-577) declared `write_census` against the four stores it names. v2597 (REG-578)
  registered `board_sync.py:REPO` and found a HALF-redirect — patching `REPO` leaves `TASKS`
  on his real file. v2598 (REG-579) gave the swallow ratchet a per-FILE baseline, then used
  it to name and FIX all four sites: 78 → 74, exactly the baseline. v2599 (REG-580) closed the
  last TWO code gates: `test_heart` pinned a phrase while the code grew a second branch, and
  `test_reachability` flagged `window` — captured from the environment probe — while the real
  symbol `window._gUniqueRoster` IS declared; its diagnostic was also fabricating the operator
  and now quotes the source line. ✅ **SEVEN OF EIGHT CLOSED, all verified green on the pushed
  bytes (39afd05a).** The eighth is `human-eyes` — **HIS, not code**: 3 briefs asked and never
  answered past 24h (GB-L-7 51.2h · GB-L-6 63.9h · GB-L-5 64.1h).
  **None is caused by v2593/v2594** — six fail identically on a clean
  `origin/main` worktree, and `printer_wilson` imports none of the nine files those commits touched.
  Named individually so none hides in the total:
  · **`printer_wilson` — `reachraises 0/40 LEAKS`**, the one axis that fails: when `printer_reach`
    raises, EXTRACT must go UNKNOWN and is instead permissive. `test_printer` fails on the SAME
    station (`'SHELF-WIDE' not found`), so these are one defect seen twice. ⚠ It is INVISIBLE in a
    fresh worktree: with no reels that axis gets 0 attempts and the gate reports PROVEN 5/5. A gate
    that can only fail where his data lives will read green on every clean checkout.
  · **`test_store_owners`** — `write_census` (v2589) touches four stores and was never declared as
    their toucher. Small and real: the declaration owes an entry.
  · **`human-eyes`** — NOT a code defect. It is the ledger reporting that **3 briefs have been asked
    and never answered past 24h**: GB-L-7 51.2h, GB-L-6 63.9h, GB-L-5 64.1h. 8 recorded · 2 answered
    with a LOOK · 3 still owed. ⚠ It SKIPS on a venue with no ledger and says *"Not a pass"* — so it
    is structurally incapable of going red anywhere except his machine.
  Owed: fix them, or state per gate why a red is correct. **A gate set nothing runs is a gate set
  that has stopped measuring**, and this one had drifted to eight without a single push noticing.

- ~~**A `record()` row bypasses the PROVES allow-list entirely.**~~ ✅ **CLOSED v2612 (REG-591)** —
  `record()` now requires a declared `src` that PROVES the lock. The reader still accepts src-less
  historical rows, because rejecting them fails the whole read (REG-575). ⚠ Fixing it reintroduced
  REG-575 **twice** — `_row_fault` and `_fold` both keyed on `src` to mean "aggregate" — and both
  now key on AGGREGATE vs EVENT. Verified behaviour-neutral on his ledger.

- **ORIGINAL, kept for the record:** A `record()` row bypasses the PROVES allow-list entirely. Found 2026-09-04 fixing REG-575.
  `bank()` refuses any (src, lock) pair the allow-list does not declare — the rule that stops one
  surface's sabotage opening another surface's lock, which matters most for `prune.arm` because
  footage has no undo. A `record()` row carries no `src` at all, so that check cannot be applied to
  it. Safe **today** only because `record()` has zero production callers; the first caller added
  makes it possible to credit any lock from anywhere. Owed: either give `record()` a declared `src`
  (a signature change, and `test_self_arming`'s `put()` helper writes that shape too), or state in
  the module that `record()` is not an evidence writer and route every harness through `bank()`.

- ~~**REG-569…573 are cited in shipped code and have NO entry in `BUGS.md`.**~~ ✅ **WRITTEN UP**
  2026-09-04 from the guards that already existed: REG-570 (a fixture could not redirect the
  deleter's ledgers, so every sabotage aimed at the chooser was graded against live data),
  REG-571 (junk dirs ate the recent shield, eligible 2→5, and the coverage line still read
  `recent: 3`), REG-572 (a negative `keep_recent` was no shield at all), REG-573 (a boolean
  rendered as a page count on an irreversible act, then the error swallowed so the console showed
  a healthy line from a measurement that had stopped). ⚠ **REG-569 was never allocated** — the gap
  is left as a gap rather than reused. —— ORIGINAL: **REG-569…573 are cited in shipped code and have NO entry in `BUGS.md`.** Found 2026-09-04 while
  logging REG-574: `tv/reel_retention.py`, `tv/test_reel_retention.py`, `tv/control_app.py` and
  `tv/self_arming.py` all cite REG-570/571/572/573, the log's highest entry is REG-568, and REG-569
  was never allocated at all. The convention is that `BUGS.md` is the record; a number that lives
  only in a comment is a citation pointing at nothing, which is exactly the failure the duplicate-
  number warning at the top of that file exists to prevent. **Drift I introduced this session** —
  the fixes are real and guarded, the log entries were skipped. Owed: write the four entries from
  the guards that already exist, or renumber if any turns out to be one defect counted twice.
- ~~**The render gate does not cover what I changed.**~~ **BOTH HALVES CLOSED.** The silent
  re-baseline was **v2567** (REG-568): `--bless` merged with a plain `dict.update()` and would take
  a LOWER number, so a bless after a real coverage loss adopted the loss as the new normal —
  reproduced at floor 65 / measured 12 / **written 12**. Lowering is no longer forbidden, it is no
  longer *silent*. The **lock chips** now have a target (`bc5fc44c`, committed, awaiting the next
  batched push): measured cold over CDP rather than assumed — all four chips exist and carry a real
  state, and `lock-vault` reads 0x0 only because its section is `display:none`. ⚠ **The target's
  first two versions refused and BOTH TIMES IT WAS MY INSTRUMENT**, not his console: demanding all
  four paint at once measured *which pane starts active*, a thing this target was never asked about.
  The contract now splits destruction/statelessness (asked of all four, in the DOM — a destroyed
  node has no rect to be wrong) from collapse (asked only of the chips on screen). 3 sabotages,
  3 RED, with a baseline.
- ~~**A2's next step:** the sabotage harnesses throw every result away, so every score is null.~~
  **THIS PREMISE IS REFUTED — measured 2026-09-04.** The banking join was built across v2444-v2501
  and v2487; `self_arming.bank()` has five callers today (`prune_wilson`, `hover_wilson`,
  `sweep_wilson`, `route_wilson`, `run_gates`). The report reads **13 of 14 locks OPEN**, every one
  on a real ledger: `miniauto.run` 55/55, `prune.arm` 48/48, `vault.apply` 24/24,
  `vault.sweep_start` 16/16, the nine routes 4/4→7/7. The 14th, `vault.forget`, is **UNPROVEN by
  construction and permanently so** — 8 lines, 0 raises, no refusal path, so no sabotage can produce
  evidence in either direction. `n=0` there is the correct final state, not an owed harness.
- **🖨🌊 THE PRINTER AND THE RIVER — RE-MEASURED 2026-09-04 EVENING. TWO OF THE FIVE ANSWERS BELOW
  HAVE SINCE BECOME FALSE, and they are struck in place rather than quietly edited.**
  · ~~*"has the printer been tested and hardened?" — NO LOCK AT ALL… not one names the printer.*~~
    ✅ **NO LONGER TRUE.** v2570 added `printer.stream` to the table and `tv/printer_wilson.py`
    sabotages it along five axes. Measured now: **OPEN, 83 of 83 refused, wilson 0.956.** It is in
    the table, it has a sabotage record, and it opened itself. (Still not HARDENED — one kind.)
  · ~~*"routed to their relevant end zone?" — EXTRACT is UNREACHABLE for all 40… the printer may
    act on ZERO of 40 reels.*~~ ✅ **NO LONGER TRUE.** v2572 gave EXTRACT a per-reel owner
    (`extract_gap`) instead of one shelf-wide word. Measured now: **RECOVERABLE 3 · NO_NAMES 12 ·
    UNSEALED 25.** Three reels are recoverable, not zero. ⚠ **OUT is still UNDECIDED for all 40**,
    and that half of the bullet stands — A15 never says which door decides *clean*, and it gates
    the prune.
  · ⚠ **STILL TRUE, re-measured — AND IT IS NOT OWED WORK, which is how I first framed it.**
    `per_reel_routes` reports **UNEXERCISED**: all 28 content-routed reels on his shelf carry the
    SAME tag, `zero-pages`, and one route is a queue rather than a divergence. I went to build the
    control that would tell "working but unexercised" from "hardwired to one branch" — **and it
    already exists**. `test_per_reel_routes` has 7 cases including
    `test_TWO_distinct_content_routes_reach_EARNED`, whose docstring states the reasoning outright:
    *"⚠ BASELINE: if nothing could ever reach EARNED, UNEXERCISED is not a measurement."* It feeds
    two reels with two tags and asserts EARNED with 2 distinct routes. **The mechanism is proven
    both ways.** Measured alongside it: **5 content-capable tags exist** (`eligible`,
    `never-chronicle-swept`, `rows-not-banked`, `vault-owes`, `zero-pages`) against `MIN_DISTINCT
    = 2`, so divergence is reachable and this is an honest fact about HIS DATA, not a gap.
  · ⚠ **AND THE ORIGINAL ANSWER TO THE FIRST QUESTION STANDS AND IS WORTH KEEPING:** the 410
    deleted reels went through the older read+seal path because **the printer did not exist yet**
    — it landed 2026-09-04 05:22 and they were deleted 2026-08-24 → 2026-09-01. Nothing about
    those deletions can be attributed to it.

  **ORIGINAL, kept in full:**

- **🖨🌊 THE PRINTER AND THE RIVER, PROBED 2026-09-04 — his questions, answered with numbers.**
  · **"did those reels get processed through the 3D/4D printer?" — NO, AND THEY COULD NOT HAVE.**
    The printer landed **2026-09-04 05:22** (`cb6aae55` v2544, `9f506217` v2546). The 410 were
    deleted **2026-08-24 23:49 → 2026-09-01 14:34** — three to eleven days BEFORE it existed. They
    went through the older read+seal path (*"read and sealed by BOTH lanes"*), not the five
    stations. 394 of 410 carried `pages == 0` and 406 of 410 had no `focus` — empty reels.
  · **"has the printer been tested and hardened?" — NO LOCK AT ALL.** 14 locks+routes are declared
    and **not one names the printer, the river, or reel selection**. No `*_wilson.py` sabotages it;
    the two files that match "printer" are quoting his own instruction in prose. So it has no
    sabotage record, cannot be HARDENED, and **is not even in the table.**
  · **"every reel gets the same unified logic?" — NO, measured on his 40.** IN: **38 recorder /
    2 repair** (two doors). ROUTE: **28 content / 12 policy** — 7 held as `test-fixture` (a suite
    opened it), 5 as `recent` (age); those twelve were NOT routed by what they contain. And
    `per_reel_routes` reports **UNEXERCISED**.
  · **"routed to their relevant end zone?" — THE LAST TWO STATIONS REACH NOBODY.** EXTRACT is
    **UNREACHABLE for all 40**: not one of 30 seals satisfies the extraction contract because the
    sweep never extracted `name`, so **the printer may act on ZERO of 40 reels.** OUT is
    **UNDECIDED for all 40** — A15 never says which door decides *clean* and the two candidates
    disagree; that choice is his and it gates the prune.
  · ⚠ **NET: the printer is a REPORT layer that currently cannot act on a single reel.** It walks
    all 40 and every station answers, which is the diagnostic working — but nothing downstream of
    FUNNEL can route anything anywhere yet.

- ✅ **THE PRUNE LOCK'S MISSING HALF IS CLOSED (REG-593, v2614) — AND ONE LINE OF THE ORIGINAL
  ENTRY BELOW WAS WRONG.** The entry said the positive path was the next evidence needed. It was
  right about the SWITCH and wrong about the SELECTION:
  · **THE SWITCH — real gap, now closed.** Every axis asserted a refusal, and a stub hardwired to
    `(False, …)` scored **identically: 48/48 either way**. A baseline now requires the guard to
    PERMIT when every precondition is met; if it cannot, no claim reads PROVEN **and the run banks
    nothing** (the first cut gated only the printed verdict — REG-593's second half).
  · **THE SELECTION — ALREADY TESTED, and I said otherwise.** `test_reel_retention` has **44
    tests**, including `test_it_selects_only_a_reel_BOTH_lanes_have_sealed_with_evidence`: four
    reels, only the correct one chosen, every rejection carrying its reason (`0 pages`, `VAULT`,
    `never chronicle-swept`). It has worked since v2575 fixed the fixture isolation (REG-570).
    **"Zero of 48 test that when it says YES it deletes the RIGHT thing" was true of THIS harness
    and not of the repo** — the proof lives in another suite, and I repeated the narrower claim as
    if it were the wider one.
  · **WHAT ACTUALLY REMAINS is HARDENED, and it is his:** `prune.arm` is OPEN at wilson 0.926,
    confluence 1.80, kinds `['cross-family','sabotage']` — **0.70 short**, and `live` alone closes
    it. Whether that third kind may be earned by running the existing axes against a live process
    is the independence question his A2·HARD row already holds, and re-running one instrument in a
    new hat would be manufactured confluence on the one door with no undo.

- **⚠⚠ THE PRUNE LOCK HAS ONLY EVER PROVEN HALF ITS CONTRACT — measured 2026-09-04, and it is
  the better next step than anything the `live` question was about.** His question was exactly
  right: *"prune.armed? OPEN but its stick locked right? like has it proven itself to work already
  the pruning and optimizing?"*
  · **NOT ARMED.** `may()` has ZERO production callers (only `test_self_arming.py`), and
    `_PRUNE_SAFE_TO_RUN = False` (`control_app.py:14423`). The badge and the arming are two
    different switches, and only the badge moved.
  · **THE DELETING HAS GENUINELY RUN**, and leaves a complete trail: **410 reels, 5,768 MB
    (5.63 GB), 2026-08-24 23:49 → 2026-09-01 14:34 across 5 days, 410 of 410 dated, 0 rows with
    `mb == 0`**, 394 reading *"read (0 pages) and sealed by BOTH lanes"*.
  · **BUT ALL 48 SABOTAGES ARE MUST-REFUSE CASES.** `_refused()` counts only the `False` arm, and
    all four axes (offspelling, worldunknown, worldraises, worldshapeless) assert a refusal.
    **Zero of 48 test that when it says YES it deletes the RIGHT thing.** The 0.926 means *"it
    correctly says no under 48 kinds of pressure"* — it says nothing about the yes, and **arming is
    exactly the act of trusting the yes.**
  · **SO THE NEXT EVIDENCE IS THE POSITIVE PATH, not a third label.** It is a genuinely new axis
    rather than the relabelling the `live` review refused, it is the half that arming depends on,
    and it can be done safely by testing the DECISION and never the action.

- **WHAT ACTUALLY REMAINS OF A2: nothing is HARDENED**, and one lock is close. HARDENED needs
  wilson ≥ 0.900 **and confluence ≥ 2.50** — three genuinely independent KINDS, because Wilson
  counts how many looks agreed and never whether they were the same look repeated. Measured
  distance for every lock:
  · **`prune.arm` — wilson 0.926 (clears 0.900), confluence 1.80, ONE kind short.** `live` (+0.70)
    would land it on exactly 2.50 and make it the first HARDENED lock in the system.
  · `vault.apply` — needs `cross-family` **and** wilson +0.038 (more n).
  · every other lock needs TWO more kinds, and most need substantial n as well.
  ⚠ **`prune.arm` guards the deleter — the one door with no undo — so the question is not whether a
  `live` kind can be banked but whether it would be an INDEPENDENT LOOK.** Re-running the same four
  axes against a live process is "one proof wearing four hats" in `self_arming`'s own words, and
  banking it would harden the deleter on fabricated confluence. That judgment is under adversarial
  review before any harness is written; the honest outcomes include DO-NOT-BUILD.

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
**Topic:** ARCHITECTURE · **Progress:** 1/3 · **MEASURED PROPERLY IN v2500, and this claim has now moved twice.** v2493 said A1 was "proven NOT a naming problem"; v2495 retracted that citing `shadowWatch == tvd-shadow-watch` — but that probe called `heart.snapshot()`, which DOES NOT EXIST, got nothing, and fell through to a fallback list of names I had typed into the probe myself. ⚠ I measured my own fallback and published it as a fact about his console. **The real numbers, against `heart.vessels()`: 11 lane names, 65 organ-published names, ZERO exact matches, and 2 of 11 lanes matched by the resolver** — `tvd-shadow-watch` ← *shadow watch* (console_doctor) and *shadowWatch* (health_engine); `tvd-version-drift` ← *version drift*. So A1 is PARTLY a naming problem, 2 of 11; the other 9 lanes have no organ publishing anything under their name, which is the missing SCORER exactly as this task always said. It only became measurable because v2496 gave console_doctor a report(). ⚠ And the vessel→watcher link needs NO resolver: 11 of 21 vessel rows already name their own watcher. · v2485 made the heart stop calling unreachable work 'owed'. **MEASURED v2521 — the scorer is not missing WORK, it is missing EVIDENCE.** Only **2 of 11** watcher lanes have anything published under their name (`tvd-shadow-watch`, `tvd-version-drift`); the other 9 have nothing. ⚠⚠ AND NAMING IS NOT SCORING: `health_engine` reports `shadowWatch` **state=ok** while its own line says *"the shadow reader is switched OFF, so nothing is watching for the game"* — so a scorer built on organ states would have reported a SWITCHED-OFF LANE AS FLOWING, and it would have looked like A1 finally working. `ok` is a verdict on the CHECK, not evidence that the lane ran. **✅ HIS RULING, 2026-09-04** — *"we can do whats needed.. like vault manager does need that wiring there i think.. like the items coming in and out"*, then *"I DO NOT want this to randomly just connect wires to it if theres no need dont do it"*. **MEASURED BEFORE WIRING, AND THE MEASUREMENT CANCELLED THE HEARTBEAT:** every vault in/out lane already leaves a DATED row — `vault_swept.json` 30 of 30 dated, `retro_triage.json` 437 of 437, `reel_tombstones.json` **410 reels, 410 dated**, spanning 244h→61h ago. A heartbeat would be a SECOND COPY of a fact already on disk, so it was NOT built, and FLOWING for those lanes can be derived from the stores that already exist. ⚠ My first tombstone reading said "0 dated" and that was MY INSTRUMENT — the file is `{"reels": [...]}` and my loop read the list as a row. **WHAT WAS REAL (v2539): `startedTs` was read from two keys no reel index has ever carried (0 of 40) and wrote None 410 times out of 410** — so the one door with no undo never recorded HOW OLD the footage was. Fixed from the frame names (40 of 40). **AND HIS SECOND HALF — *"connect it to the heart of the console that way we would have caught it"*: `tv/dead_field.py` is joined to the heart payload AND on PIXELS (new `render_check` target `heart`, 59/59 painted at five widths, floor blessed), and it catches that field on his real store.** ⚠ The photograph then found a 120px band where the heart's diagram belongs carrying **min == max == 17, ZERO ink** — measured on the PNG, and a cold cross-family look DISAGREED and was wrong. Logged REG-539; cause NOT established. **STILL OPEN: should the other nine watcher lanes — the ones with nothing published under their name — get a heartbeat, or stay unreachable?**SCOPE CUT 2026-09-03, his call — "scratch it off the list":** *the four organs on every surface* is OUT. A3 measured the ground truth — 44 surfaces, most of them internal loops like `_bridge_prober` and `_chron_autoread_loop`; four organs each is **176 wirings** for no gain. What replaces it: declare in code which surfaces can **lose data or show him a number**, wire those, and mark the rest out of scope WITH A STATED REASON, so the matrix stops being a 44-row guilt list. Denominator moved 4 → 3

> *"self-proving gaps i want taken care of everywhere all round the console i want this logic and
> its own logic coded proving itself! and if it drifts it gets flagged accoridngly and designed
> like we designed to either get fixed or we fix it and the doctor it to be watchdgoged and
> connected to the heart to fix iteself by hardcode design once everything is fixed and locked in
> maybe not just yet the self healing... but in the future no reason for not"*

The flagship. Every gap on the console carries its own proof, flags its own drift, and is wired to
THE HEART (eagle eye · watchdog · corroborator · doctor). ⚠ **Self-healing is explicitly NOT yet** —
he said "maybe not just yet". Build the proving and the flagging; leave the self-repair for later.

## A2 · WILSON EVERYWHERE — and make it actually mean something · 2026-08-30 09:25 + 09:30

> ⚠ **RE-MEASURED 2026-09-04 — A2 IS DONE, AND THE BRIEF THAT KEEPS ASKING FOR IT IS STALE.** The
> recurring instruction still says *"five self-arming locks sitting at n=0 UNPROVEN"*. Against
> `self_arming.report()` today: **14 of 15 locks are OPEN with real evidence** — `printer.stream`
> 83/83 w=0.956, `miniauto.run` 55/55 w=0.935, `prune.arm` 48/48 w=0.926, `vault.apply` 24/24,
> `vault.sweep_start` 16/16, and the nine routes at 4-7 each. **Exactly ONE is at n=0**, and it is
> `vault.forget`, which declares `unprovable:` in its own spec — *"the door has no refusal path by
> design… gating it would be a cage"* — with `provable: False` published, a distinct `why`, and
> three guards pinning that the report, the status trim AND the renderer all tell UNTESTED apart
> from UNPROVABLE. **n=0 there is the correct and final state, not a harness anyone still owes.**
>
> The hardening report is honest too, which is why no work was invented: every lock names
> `kindsWouldClose: ["cross-family", "live"]` and separates the two halves in its own sentence, so
> `moreRefusalsNeeded: 30` cannot be misread as *"30 sabotages and it hardens"* — it closes only
> the wilson half.
>
> ⚠⚠ **AND HIS QUESTION RE-OPENED SOMETHING BIGGER, 2026-09-04** — *"just check and make sure its
> really unlocked and not fabricated… its logical there are some routes that were working correctly
> before the HEART"*. He was right to ask. A fleet audited all five harnesses and an adversarial
> reviewer re-measured each; **all five findings stood and one found MORE inflation.** Nothing is
> fabricated — every refusal is real — but **four of the six locks would not clear their own bar if
> the repeated trials were counted once**, and the worst offender guards the deleter. Full table and
> evidence in `BUGS.md` **REG-598** (one source, not copied here). No bar was changed and no lock
> was closed: the bars are his, the locks are badges, and what changed is that both numbers are now
> published so a score resting on repetition says so.
>
> ⚠⚠ **AND THE FLEET FOUND A WORSE DEFECT THAN INFLATION — `BUGS.md` REG-600, LOGGED NOT FIXED.**
> **48 of `miniauto.run`'s 55 "sabotages" are AGREEMENTS.** `probe_coordinate` displaces a cell
> centre by one full cell and requires `cell_of()` to return a different cell — but `cell_of` is a
> pure coordinate converter with no guard behaviour there, the displaced point is a perfectly VALID
> point in the neighbouring cell, and returning it is its **ordinary correct answer**. A
> floor-division unit assertion counted as 48 sabotage refusals. `probe_anchor` is an agreement
> counter **by construction** and banks 0 only by accident — calibrate its offset and it silently
> starts banking agreements as refusals. ✅ **His read stands: MINI AUTO was working before the
> heart and still is** — it clears on every honest count. What was wrong is the number claiming more
> evidence than existed.
>
> ⚠ **FIRST TO LOOK AT IS NOT THAT ONE.** `vault.sweep_start` guards *"starts a paid sweep"* — his
> money — on **2 distinct attacks, honest Wilson 0.3424 against a 0.510 bar.** It does not clear.
>
> **WHAT EACH LOCK GUARDS, in the code's own words** — he asked, so it is written down here rather
> than re-derived: `prune.arm` *"deletes footage — there is no undo"* · `miniauto.run` *"moves the
> pointer over his stash and films the tooltips"* · `printer.stream` *"walks every reel from the
> door to the far end"* · `vault.apply` *"mules items between characters"* · `vault.sweep_start`
> *"starts a paid sweep"*. **The nine routes are not engines — they are his three numbers (99 / 135
> / 403) on three screens**, CHRONICLE / FLEET / ROSTER, and the sabotage deletes the evidence a
> lane claims to have found to see whether the lane notices. What remains is a SECOND KIND of evidence for 12 locks, and that is the
> independence question already held as **his call**, not something to build unasked.
>
> **CF-13 re-measured the same day and is also done.** `undeclared_reach_abilities` was correct and
> uncalled — *a measurement computed correctly and read by nobody is the same as one never taken*.
> `control_app.scope_reach_state()` now joins it as EVIDENCE, honours its author's verbatim ruling
> (*"DO NOT PROMOTE THIS TO A FAILING GATE"*), publishes each row's reach so noise looks like noise,
> and `narrow` is stated in its own comment to be a reading aid that decides nothing.
> `test_heart_surface.py` guards that it still has a caller outside its own tests.

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
**Topic:** ARCHITECTURE · **Progress:** 3/3 ✅ · v2497 MADE THE JOIN — the 9 MISNAMED were ONE dropped qualifier: `_corr()` flattened three route modules into one set of bare names and threw away which lane each came from. All 9 are COVERED now, and exactly those 9. ⚠ The first form joined only 6 — the 3 holdouts named a real split: chronicle/roster spell their routes SINGULAR, fleet spells them PLURAL. That is logged as REG-470. ✅ **CLOSED AS CONTAINED, v2629 — and the measurement argued against the obvious fix.** `one_name` ALREADY joins the two spellings (`same_thing('fleet.runewords','chronicle.runeword')` is True), nothing mis-joins today, and the self-arming ledger is keyed on the RAW names — so renaming `fleet.runewords` would **orphan its banked rows and drop that lock to UNPROVEN**. The inconsistency stays NAMED; what ships is a guard that stops a THIRD spelling arriving. ⚠ Its own sabotage found a hole in it first: an `or tail` fallback made every misspelling pass. · v2496 made the doctor's column ANSWERABLE — `console_doctor.report()` now names all 34 checks without touching the window he is looking at (`run()` posts to /api/board_ownership, which evaluates JS in his live board), and the matrix learned to read `check`. ⚠ THAT ALONE WOULD HAVE MADE THE TABLE LIE: the doctor names CONCERNS and the surfaces are CODE OBJECTS, zero of 34 resolve to any of 44, so the column filled with 44 confident ABSENT cells. An incomparable column now says UNKNOWN with its reason, and the summary states how many organs its verdict rests on (1 of 4). REMAINING: make the join so the 9 MISNAMED become COVERED. · v2491 MEASURED the matrix — 44 surfaces × 4 organs, and the holes are three different things: 9 MISNAMED (the organ watches it under another name — a join nobody made, and how the table came to look empty), 1 organ UNKNOWN everywhere (console_doctor has no report), the rest genuinely ABSENT. REMAINING: make the join so MISNAMED becomes COVERED, and give console_doctor a report so its column is answerable.

> *"fix those gaps and anywhere else.. make it unified and logical and coded properly with
> watchdogged and eagle eyed and doctor and corraborotror"*

Said over a table of surfaces against capabilities that was mostly holes — `surfaces registry`
empty across every column, `stash_eye grid` empty across every column, `enlarge (crop + …)` empty,
`OCR worker` present in exactly one. Every surface gets the same four organs, or it is honestly
marked as not having them.

## A4 · THE 3D / 4D PRINTER PIPELINE · 2026-09-01 10:49
**Topic:** BACKEND · **Progress:** 1/3 · ⭐ **A10 SHIPPED in v2505** (`tv/reel_river.py`) — the acceptance test and the end-to-end probe both exist now. v2503 measured what the pipeline can act on AT ALL: 0 of 30 seals satisfy the extraction contract (22 fail on `name`, which only appears in a hover tooltip), so the A4 contradiction is structurally UNREACHABLE rather than absent and a grid-only reel can never be judged disposable. v2505 walks each reel naming the decider and question per stage. REMAINING: the unified printer itself (A7·A8·A15) — one path, templates inside the routing.
**Topic:** BACKEND · **Progress:** 2/3 · ✅ **THE PRINTER ITSELF SHIPPED v2544** (`tv/printer.py`), joined to `/api/heart` and photographed — his instruction: *"3d 4d printer connected to the heart of the console and the reels like we said going in unified and getting processed and routed out clean on the other end of the stream"*. Five stations, each QUOTING its owner and deriving nothing: **IN** recorder 38 / repair 2 · **FUNNEL** releasable 12 / swept 28 · **ROUTE** content 28 / policy 12 · **EXTRACT** UNREACHABLE all 40 · **OUT** UNDECIDED all 40. ⚠⚠ The far end is UNDECIDED for every reel BY DESIGN — A15 never says which door decides *clean*, and conjoining the two is the collapse v2312 withdrew; **that choice is his and it gates the prune (task 146)**. ⚠ It prints nothing and deletes nothing; a guard asserts the module contains no delete and no write mode. **On pixels:** the heart target rose 59 → 65 painted at five widths, 0 clipped, floor blessed; a cold cross-family read of the rendered row caught *"UNREACHABLE 40"* being parseable as *"there are no reels"* — it reads `UNREACHABLE — all 40` now. 4 sabotages, 4 RED. EARLIER: v2503 measured what the pipeline can act on at all (0 of 30 seals satisfy the extraction contract); v2505 walks each reel naming the decider and question per stage. REMAINING: A15's *clean* definition, which is his.

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
**Topic:** BACKEND · **Progress:** ✅ **HIS CALL TAKEN — v2578.** *"the templates should sort of decide for it... if no inventory is there or a stash template open.. then it can classify it accordingly"*, then *"BOTH logics intertwined... not just one rules out"*. `lane_at_graded` returns the answer WITH its grade: **CONTAINED** (a read covers the moment — unchanged, and still the only grade that opens a door alone) · **RULED_OUT** (the reel never opened a container ANYWHERE, so no moment in it can be a possession — a sound NEGATIVE, not a guess) · **INHERITED** (between two reads of the same container, inside `reel_segments`' OWN one-visit window — real evidence and WEAKER, graded rather than dressed up) · **UNSETTLED**. ⚠ `lane_at` is deliberately UNCHANGED: every existing caller, including the vault door that refuses claims, keeps the strict answer it was written against. ⚠⚠ **AND A NUMBER I PUBLISHED THE SAME HOUR WAS MY OWN BUG** — I reported 325 sound negatives; `lane_at` returns None for TWO reasons (no read covers the moment, and a read DOES cover it but that activity is not possession), so 326 COVERED moments were re-graded as ruled-out-by-template. Keyed on `activity_at` now: contained 7→326, ruled-out 325→**11**, unsettled 2436→2434. The intertwined logic adds ELEVEN sound negatives and a graded inherited path, not 325. ⚠ Two of my own guards were INERT and the sabotages said so. **REMAINING (unchanged):** widen the walk to the 28% of rows that nest differently. ⚠ It cannot recover the past — a row whose reel is gone stays without a loc for ever. Historical detail: ⚠ **WIRED BUT INERT (v2515 + v2517)** — **the INTAKE half only.** ⚠⚠ MY v2515 CLAIM THAT THIS "stops all future loss" WAS WRONG and is corrected here: the stamp is correctly wired and **stamps 0 of 14,034 rows**, because `_sighting_loc` returns None for every one. v2517 found why — the sighting carries `reel_<session>` while the journal is keyed `<session>`, so **that gate has resolved NOTHING for a stored sighting since v2353**, the exact failure its own docstring warns about. Bridging the prefix collapsed `no_segments` 10,101 → 1,353, and resolution is STILL 0: necessary, not sufficient. ⚠ The stamper also reaches only 10,101 of 14,034 rows — 28% of the store nests differently and is silently skipped. **THE SECOND REFUSAL IS NAMED (v2519):** `lane_at` asks which segment CONTAINS the moment, and segments are the INSTANTS OF READS, not the intervals between them — measured, one session covers **3.52%** of its span and **13 of 483 frames (2.69%)** fall inside a segment. Store-wide, **8,748 of 10,101 lookups now FIND their segments and still cannot answer**. That is not a defect in the resolver; it is what containment means against instantaneous segments. ⚠ **HIS CALL:** widening it to *the nearest read* would make provenance a GUESS, and this answer feeds a door that refuses vault claims — so it is put to him rather than changed underneath him. **THE QUESTION:** should a frame captured between two reads inherit the lane of the nearest read (and within what window), or stay UNKNOWN? REMAINING besides that: widen the walk to the 28% of rows that nest differently. `_sighting_loc` has answered *where a name was seen* since v2353 and **nothing kept the answer**: measured on the live store, **0 of 14,034 evidence rows carry a persisted `loc`**, while **39 reels are named and 3 still exist — 92% gone**, so only 25% of rows could ever have it re-derived. Computed, rendered, thrown away. The stamp now runs at evidence-merge time, the last moment the reel is reliably present. ⚠ THE FIGURES BELOW WERE UNDERSTATED — 20/6/70% was the earlier reading; it is 39/3/92% now. ⚠ It cannot recover the past: a row whose reel is gone stays without a loc for ever, which is the 75%. Future loss only.
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
**Topic:** BACKEND · **Progress:** ✅ **2/2 — v2589 TOOK THE MEASUREMENT** (`tv/write_census.py`). A7's own remaining line was *"the per-store answer is a measurement NOBODY HAS TAKEN"*, after THREE instruments each returned a zero that measured themselves. Answered by OBSERVATION: arm the witness, run something that really writes, read back who did it. **MEASURED `retro_triage.json` → written by `retro_triage`, mode=replace, retro_triage.py:149** — and `mode=replace` is the tmp-then-move write all three earlier instruments missed. The observed writer IS the declared owner, so `store_owners`' claim is confirmed at RUNTIME rather than by coupling. The other four stores say **NOT EXERCISED with the reason** — a tombstone needs a real deletion and the prune stays OFF; vault_accum/vault_swept need a PAID sweep; chron_evidence needs a real read — never a zero that would read like an answer. ⚠ It never touches his stores: every exercise runs against a scratch root, and a writer's identity does not change with the path. ⚠⚠ **AND IT SHIPPED A FALSE GREEN I CAUGHT BEFORE PUSHING** — it read `store_owners.report()`, which does not exist and returns `{}`, so every agreement check was None, no disagreement could exist, and the summary announced agreement having compared NOTHING. It reads `STORES` now and an UNCHECKED comparison says so. Registered as a gate. Historical detail: **v2507 made A7 CHECKABLE** (`tv/store_owners.py`): one declared OWNER per reel store, every other module a declared reader WITH A REASON, and a module that starts touching a store fails until it is argued in. 4 stores, owners retro_triage · reel_retention · vault_retro · frame_authority, every toucher accounted for (3/3/7/9). ⚠ IT REPORTS COUPLING, NOT WRITES, and says so — TWO attempts to measure writers returned ZERO for all four stores (a filename-adjacency grep, then an AST walk resolving path constants), because paths are bound in helpers and threaded through arguments. Both zeros measured the instrument, so A7 is NOT scoped on a number I do not trust. ⚠ The registry caught ITSELF on its first run. **v2527 BUILT THE RUNTIME TECHNIQUE** (`tv/write_witness.py`): it patches `open`, `io.open` and `os.replace` to RECORD and calls straight through, attributing each write to the nearest real module. ⚠⚠ ITS OWN DEMO CAUGHT IT BLIND — patching only `builtins.open` missed `io.open`, so a module whose job is counting writers reported ZERO for a store it had just watched being written, which would have been the THIRD zero in this task. ⚠ It also named `<std` as a module, because `abspath('<stdin>')` lands inside the tree. ⚠ And the write that MATTERS never opens the store: these are written to `<name>.tmp` and MOVED, so watching only `open` sees the tmp and never the store. ⚠⚠ IT IS AN INSTRUMENT, NOT A MEASUREMENT — a sweep has to run while it is on, and the per-store answer is a measurement NOBODY HAS TAKEN. REMAINING: run it during a real sweep (a write hook or an owner-mediated API), not a static walk

> *"all reels need to be processed the same way all unified logic"*

No reel gets a special path, a bypass, or a second implementation. One pipeline, one set of rules,
every reel. Any lane that processes a reel differently is either folded in or declared, in code,
as a deliberate exception with a reason.

## A8 · THE TEMPLATES LIVE **INSIDE** THE PRINTER'S FILTERING AND ROUTING · 2026-09-01 19:0x
**Topic:** BACKEND · **Progress:** ✅ **1/1 SHIPPED v2523** — its testable form was *"if a template can be removed without the routing changing, it is not wired in"*. ⚠⚠ MEASURED, AND IT WAS THE INVERSE: `resolve_tab` named ANY tab in the marker dict, including one with **no template band at all** — handed `{'tab_marker': {'hardcore': 0.05}}` it answered `hardcore`. Nothing was wrong on this tree (geometry_signals only produces TAB_BANDS keys), but the router's correctness rested on an upstream convention it did not check. An undeclared tab is dropped WITH ITS REASON now, and A8's own test runs literally: remove the `sets` template and `sets` becomes unnameable. ⚠ One deliberate behaviour change pinned: a stray key used to make a real read AMBIGUOUS and refuse; it is dropped now and the real marker wins — two REAL tabs lit still refuse

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
**Topic:** ARCHITECTURE · **Progress:** measured 2026-09-04 · **30 thread targets · 11 supervised · 8 unwatched loops** (the line below said 28/11/7 and had gone stale AGAIN — the third time this number has drifted in this file, which is why the census carries its own `--prove`). ⚠⚠ **AND THE EIGHT ARE NOT WHAT THEY LOOK LIKE: SIX OF THEM ARE SUPERVISORS.** `_console_rescue_loop` · `_mini_watchdog` · `_orphan_exit_loop` · `_orphan_watch` · `_console_beacon_loop` · `_bridge_prober` all watch something else; only `_engine_driver` and `_kai_closer_loop` are work. **The console supervises its WORK lanes and not its WATCHERS** — and `_console_rescue_loop` is the watchdog that rescued his black window on 2026-09-04, so if it dies nothing notices and the rescue silently stops working. The census names which unwatched lane is a supervisor now, because a flat list of eight could not say that. ✅ **CLOSED v2621+v2630 — and it never needed the risky change.** Registering them would have meant moving thread starts into `start_background_watchers`; the heart's own text already said what was actually missing — *"a different mechanism (a peer, a heartbeat file, a second process), not the watcher the other DARK rows are waiting for"*. **A liveness stamp read by the heart IS that mechanism, and it changes no thread start.** ⚠ It was HALF DONE first: three of six supervisors stamped and three did not, which is the worse state because the unwired half is the one nobody notices — the same shape as stopping at five of six harnesses in REG-598. All wired (REG-611), and the guard asks the CENSUS for its list rather than a typed one, so a loop added later is covered the day it appears. ⚠ `_engine_driver` and `_kai_closer_loop` declare no fixed period, so they report UNTIMED — age known, staleness not decidable

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
**Topic:** BACKEND · **Progress:** 4/5 · **v2525 tested the clause that CAN be tested** — *the route is derived from the CONTENT, never guessed from a declared stamp* (`tv/declared_vs_content.py`). ⚠⚠ THE ANSWER IS **UNTESTABLE ON HIS CORPUS**, and that is the finding: 40 reel dirs, 40 with an index.json, and exactly **1 declaring a chronicle focus — carrying 0 surveyed panels**. Zero disagreements over a sample that cannot disagree measures the SAMPLE; it will say AGREES the moment three declaring reels carry content, and a real disagreement outranks the floor immediately. ⚠ `chronicle_retro._declared_kind` DOES route on a declaration (it picks which sweep owns a reel; the sweep then judges content) — whether A15's letter forbids that is a judgement today's corpus cannot settle, recorded rather than decided. ⚠ And the SOURCE refuted my suspicion before publication: `_vault_lane_owes` returning True with no declared focus looks exactly like v1783 and is the deliberate safe direction — *"I could not tell must never resolve to delete it"*. **v2529 MEASURED THE LAST CLAUSE AND FOUND IT UNDEFINED:** A15 says *clean is a state the pipeline must be able to ASSERT per reel* and never says WHICH DOOR decides — the two candidates disagree on his shelf: **12 of 40 finished by the REEL door, 0 by the FRAME contract, 0 by both**. ⚠⚠ Conjoining them is exactly the collapse **v2312 attempted and WITHDREW** (v2314: they answer different questions at different granularities), so `reel_river` reports BOTH and calls neither the answer. **Defining *clean* is yours — it is a decision about what *finished* means, and it gates the prune (task 146).** **v2532 MEASURED CLAUSE 1 — ONE START POINT — ON THE ARTIFACT** (`tv/one_start_point.py`), not on a source grep, because A7 counted writers twice in this same cluster and BOTH zeros were measuring my own instrument. His 40 reels cannot do that: **40 of 40 carry the recorder's core (sessionId · n · frames)** — 38 minted by the recorder, 2 restored by the repair door, **0 born through the fixture door**, which is the fixtures-never-touch-live-data law measured on the artifact rather than asserted. ⚠ Three modules can write a reel's index.json and only ONE is a front door; counting `reel_index` (which refuses to rewrite an index that parses) as a violation would cry wolf on a healthy shelf. ⚠ A repaired index is THINNER — and I measured before claiming harm: only **3 of 40 reels carry a `blank` flag on any row, 5 frames total**, neither of them a repair, so the loss is real and its damage is not. 4 sabotages, 4 RED. **v2533 MEASURED CLAUSE 2 — ONE FUNNEL** (`tv/one_funnel.py`), and it splits in two: **THE LADDER is ONE_LADDER** (6 rungs, no rung naming two stages, no stage at two rungs, 0 reels at an untaught stage) but **THE PASSAGE is PARTIAL — only 2 of the 6 rungs leave a dated waypoint** (`retro_triage` 40/40, `vault_swept` 15/40); for the other four the order a reel travelled in is recorded NOWHERE. ⚠⚠ And occupancy is not a route: `stage` is the rung a reel is stuck BEFORE, so an empty rung means nobody is STUCK there — never that nobody passed. 3 sabotages, 3 RED. **v2534 CORRECTED CLAUSE 2's OWN PROBE** — it retyped `retro_triage.json` and `vault_swept.json`, two names their owning modules already declare. Reproduced, not imagined: rename the store and `triaged` (40 of 40 covered) silently vanishes from the dated rungs while the verdict stays PARTIAL. It quotes `retro_triage.STORE` and `frame_authority.SEAL_STORE` now, and an owner that stopped declaring one returns None WITH A REASON rather than a guessed filename. 3 sabotages, 3 RED. **v2535 MEASURED CLAUSE 3 — PER-REEL DIVERGENCE** (`tv/per_reel_routes.py`). The question is not whether reels differ — it is whether the difference is EARNED BY THE CONTENT. Measured: **28 routed by content, 12 by policy, and they are the same 28 and the same 12 as `swept`/`releasable`** — so **every reel that reached the far end got there BY POLICY** (5 recent, 7 test-fixture), and all 28 content-routed reels sit under ONE tag at ONE rung. **State: UNEXERCISED** — the content-earned divergence exists in the code and nothing on his shelf exercises it. ⚠⚠ NOT A DEFECT: `zero-pages` means *swept and found nothing*, a deliberate hold because the engine reopens those when the prompt improves; calling it a routing failure would cry wolf on a shelf behaving as designed. 4 sabotages, 4 RED. REMAINING: *clean* assertable per reel — blocked on his definition, and it gates the prune

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

## 🧭 HIS ORDER OF WORK, 2026-09-04 — and the one architectural constraint on everything new

> *"MINI-AUTO is just not complete yet, it's not been created and recalibrated.. we will get to
> that after we completely finish every tasked list and grok's handoffs in between too."*

**So MINI AUTO's rebuild is LAST**, after the task list and the Grok handoff queues. `v2621` shipped
only the RECORDER (REG-604) — inert until he runs mini auto, and the thing that makes the
recalibration possible when he does. It is not the rebuild.

> *"ON AIR and MINI regular WORK — they were designed and working products and working routes
> before all of this... everything is obviously using all harnessed techniques and logic from that.
> Any reels coming to station, the same AI and the same READERS and KAI eyes all need to be doing a
> unified sweep and a unified pass... that way the accuracy of everything else already working
> stays working, and everything being built new gets hooked up and connected to a working product
> and unified logic."*

⚠⚠ **THE CONSTRAINT ON EVERY NEW THING: reuse ON AIR's existing readers and sweep. Never a parallel
path.** ✅ **MEASURED 2026-09-04 and it currently HOLDS:** exactly **two** reader definitions —
`tv_diablo.claude_chronicle_read` and `g5_grok_eyes.g5_chronicle_read`, which is the deliberate
two-lane cross-family design — **one** lane resolver (`control_app._chron_lanes`), **4** call
sites, and **no second reader path anywhere**. `chronicle_sweep_now.py` says so in its own words:
*"It reuses control_app's OWN wiring — chronicle_sweep_start / chronicle_sweep_state."* Anything
entering at the station inherits those readers by construction.

⚠ **What is NOT unified, and is a different question:** the IN door (**38 recorder / 2 repair**) and
the ROUTE (**28 by content / 12 by POLICY**). Those are doors and routing policy, not readers — A4
already records them and they do not violate this constraint.

## 💵 HIS MONEY RULING, 2026-09-04 — spending is authorised BEHIND the proof, not instead of it

> *"whatever needs to use my money is fine as long as its working properly and coded and not looped
> and debugged obviously.. but money needs to be spent.. its doing AI reads just needs to be
> optimized and more focused reads where needed thats why we built this and still building the
> corrected architecture for it"*

**This unblocks 155, and therefore 154's remainder and 146 — but it is CONDITIONAL, and the
condition is the whole sentence.** Four words carry it: *working · coded · not looped · debugged*.
So a paid pass may run **after** the path that consumes it is proven, never as the thing that
proves it. That is the same sequencing he set for `gh #210`: *"when it does finally enter from a
session everything is clean going in and then out."*

⚠ **"NOT LOOPED" IS THE EXPENSIVE ONE AND IT HAS A SCAR.** [[paid-work-with-no-memory]] records
**3,434 paid reads for 2 sightings**, looking like healthy activity the whole time. A re-read that
cannot tell it already read something is the exact shape this ruling forbids, and it is what
`extracted: []` sealing exists to stop — a frame examined and found empty is RECORDED as examined,
so it is never paid for twice.

⚠⚠ **"FOCUSED READS WHERE NEEDED" IS A MEASUREMENT, NOT A PREFERENCE — and it is already taken:**

| | reels | what a paid pass would buy |
|---|---|---|
| never read at all | **29 of 40** | genuinely new evidence |
| sealed, nothing readable ever | 12 | **nothing** — REG-340: the name is only in a hover tooltip, so a grid-only reel can never satisfy it. A capture change, not a paid one |
| names read, no seal | 12 | **nothing new** — the reading is done; the seal is missing |
| **JOIN — sealed AND names read** | **3** | **nothing — it is FREE.** The names are on disk and the seal does not carry them |

**So the cheapest work is the 3 JOIN reels, and it costs zero.** A broad sweep across all 40 would
re-spend on 24 reels that have already given a complete answer. **Spend on the 29 that were never
read, not on the shelf.**

## 🔥 THE URGENT THREE — "task these in first urgently before the other tasks"

| # | What | State |
|---|---|---|
| **165** | **THE NEXT LOOK** — the harness has EYES AND NO HANDS. Synthetic pointer events need macOS Accessibility; without it `CGEventPost` silently succeeds and moves nothing. So Claude names the pane in CODE and a human eye photographs it. `tv/ask_view.py vault --brief HE-2` → `.view_request.json` → `view_request()` publishes 5 states on `/api/status` → the console honors it ONCE, stamps the screen, puts his tab back. Refused states (STALE/UNKNOWN/HELD/BROKEN) paint **nothing** on his screen. Contract = `gh #186`. | **SHIPPED v2399** |
| **166** | **LOCK THE NAMESPACE, and the ledger is authoritative.** His ruling: *"NO i want it locked to whats it is now"* / *"not only up — its also in the ledger with proof, that way from there it can reupdate its profile if needed"* / *"anything done manually by a human is proof and witness enough and bypassed."* PIN `I·77f64154·`, profile `main`. The law is **MONOTONIC** (may rise, never fall), not equality. | **BLOCKED — measured.** The loggers do not carry proof today: `d2r_foundLog` is 412 rows of `{name: "Jun 22, 2026 · 02:00"}`, a display string with no reel/frame/witness, and 8 of his 169 owned items have no log row at all. The rebuild he wants is right; the data cannot do it yet. |
| **167** | Show the eye in **THE FLEET** when it is live. | ✅ **SHIPPED — it was already built; v2622 fixed the defect in it.** `_eye_for_wire` (*"167 — counts only, for THE FLEET"*) has been in the beacon all along and his live row carries `eye: {"live": false, "ageMs": 0}`. ⚠ I reported it half-built off a **150-char truncated print** of `/api/fleet` and then wrote a SECOND writer — a duplicate dict key, where the last silently wins — and my own sabotage came back green, which is what exposed it (REG-605). **The real defect:** the wire called the eye live only within **6s** while the beacon carrying it fires every **240s**, so a continuously live eye reached the fleet **2.5%** of the time. Widened to 300s for the wire; `ageMs` unchanged. |

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
| **135** | Daily-pick dead branch. 3 edits + 1 spec test. ⚠ Three namespaces use `'grail'`; **only the chron-entry key may change.** | ✅ SHIPPED v2474 · measured 2026-09-04 · `bible.html` | ⚪ **none** — the undone-ness has no single string, so `tasks_freshness` reports it UNKNOWN every run rather than passing it silently. |

⚠ **#135 MEASURED DONE 2026-09-04 — this row is stale and had started to cost the work twice, which is the exact defect the note above it describes.** The third arm is IN the page: `bible.html` `dailyCreateAi` carries `else if (_rot && _rot.incomplete && _rot.incomplete.length)` under a comment naming #135, and it is JOINED — `window._chronRotation()` returns `{all, incomplete, target, sealed}`, so `.incomplete` is really published rather than read off a shape nobody sets. The spec is `tests/v2474_daily_pick_exhausted.spec.ts`, four cases, including *"the wipe arm fires ONLY when there is genuinely nothing to name"*. ⚠ Closed on what the page ASSERTS today, never on a grep count — and `tests/v135_rich_hover_tooltips.spec.ts` is a DIFFERENT thing (v135 the version, not task #135), which is exactly the kind of near-miss that would have closed this wrongly.


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
| **155** | Would spend paid reads. | ✅ **NO LONGER BLOCKED — HE DECIDED IT 2026-09-04, and the ruling is written 73 lines ABOVE this row in this same file** (§💵 HIS MONEY RULING: *"whatever needs to use my money is fine as long as its working properly and coded and not looped and debugged"*, and the section's own sentence *"This unblocks 155"*). A row cannot be blocked by a decision this file records as taken — that is a stale label, not a blocker, and it sat here for a day. **The condition, which is the whole ruling:** a paid pass runs BEHIND the proof — after the path that consumes it is proven — never as the thing that proves it. So it is sequenced after A15's *clean* definition, not blocked by his silence. **Spend on the 29 never-read reels, never a broad sweep**: 24 of the 40 return nothing new (12 sealed-unreadable is a CAPTURE change, 12 names-read is a missing seal). [[paid-work-with-no-memory]] — 3,434 paid reads bought 2 sightings. <!--fp: TASKS.md :: His money.--> |
| **154** | ⚠ **HALF LANDED (fleet-measured 2026-09-04)** — `pruned_mb=None` now passes at `control_app.py:16151`, `prunedMbInWindow` returns None rather than 0 at `:12732`, guarded by `Test154PrunedMbUnknownIsNotZero`. His live `disk_history.jsonl` shows the change taking effect: rows 0-8269 carry `prunedMb: 0` (last 2026-09-02), rows 8270+ do not. The remainder is still open. Blocked by 155. ⚠ **My own framing was RETRACTED:** `pruned_mb=0` and `hist_bytes=None` are HARDCODED at the only call site, so `prunedMb: 0` across 7,009 rows is a fact about the CALLER. "The prune has never freed a byte" is **not supported**. The real defect is that the field can never report anything. | `tv/control_app.py:14920` (writer at `:11954`) |
| **136** | ⚠⚠ **UNACTIONABLE — THE TASK ITSELF IS LOST, and that is now provable.** This row has read only *"Blocked by vault names."* since the EARLIEST tracked version of this file (`a8016ea6`, the commit that made TASKS.md tracked at all) — there has never been a description. Its content lived in the session that created it, which is exactly the loss this file's own preamble records: *"the memory queue recorded the NUMBERS and not what they meant."* **Nobody can act on it, including him.** Kept, never deleted — but it must not sit here looking like work. If he remembers what 136 was, it becomes a real row again in one sentence. | ⚠ CONTENT LOST |
| **148** | ⚠⚠ **UNACTIONABLE — THE TASK ITSELF IS LOST, and that is now provable.** This row has read only *"Blocked by vault names."* since the EARLIEST tracked version of this file (`a8016ea6`, the commit that made TASKS.md tracked at all) — there has never been a description. Its content lived in the session that created it, which is exactly the loss this file's own preamble records: *"the memory queue recorded the NUMBERS and not what they meant."* **Nobody can act on it, including him.** Kept, never deleted — but it must not sit here looking like work. If he remembers what 148 was, it becomes a real row again in one sentence. | ⚠ CONTENT LOST |

---

## 🖼 NEW — THE RENDER GATE REPORTS CLEAN ON A PAGE WITH VISIBLE CLIPPING

**Opened 2026-09-05, and it was the second-eye gate that produced it.** The pre-push hook REFUSED
v2648 because v2645 had never been looked at by a different model family. The console was rendered
at five widths, **looked at**, and three shots handed to another family COLD.

| # | What | State |
|---|---|---|
| **GATE-EYE** | At **375px** the page shows `ON AIR`/`MINI` stacked with text cut off, the AI READS bar reading **"appea / here"**, `"Failed to fetch"` sliced mid-word, and the TZ TRACKER header clipped — every item named by the cold eye and then **confirmed by looking at the PNG**. `render_check` reported **`painted 1/1 · clipped 0 · off 0 · covered 0`** at that exact width. **The structural reason:** the `console` target's selector is `sel: "#btn-mini, #btn-miniauto"`, so `painted 1/1` measured **one button** — "clipped 0" was never a claim about the page, and every defect above sits outside every target's selector. Sample ≠ verdict, on the visual gate itself. ⚠ **Seen by me, not by the eye:** the logo tile renders as a **broken-image placeholder** at every width while the harness reports `imgs 0/0` — it examined zero images. ⚠ **NOT claimed:** a page-wide probe of mine counted 14 cut / 4–9 covered per width; it does not check for a scrollable ancestor above the clipping one — the exact hole `render_check`'s own v2381 note records — so that number is **not** published as a finding. | ⚠ **HALF DONE — THE INSTRUMENT IS REPAIRED, THE DEFECTS ARE NOT.** The structural cause named in this cell was fixed by **v2650-v2651 (`34532602`)**: a whole-`page` target exists at `tv/render_check.py:395`, so `painted 1/1` no longer means "one button". With the gate able to see the page, the real numbers are **54 clipped at 375px · 5 at 901 · 1 at the wide widths**, declared per width as a FLOOR and refusing only on a RISE. The `imgs 0/0` half is also superseded — images are examined now, **4 broken of 2,399**. ⚠⚠ **So this row's remaining work is the 54/5/1 BACKLOG, not the harness** — and a row that keeps describing a fixed instrument sends the next reader to repair something already repaired. Tracked below as GATE-EYE-2. |

---

## 👁 OPEN BRIEFS — human eyes, four

| # | Brief | Needs | State |
|---|---|---|---|
| **182** | **HE-2** — what number does the VAULT pane actually display? Three sources disagree: `/api/vault_ledger` = **7**, `status.ledgerBackup.counts.owned` = **169**, what he expects = **~40-46**. | console only | **OPEN, GO given** |
| **185** | **HE-5** — is the footer hover ONE line, with everything moved into the click window? Ships in v2397. | console only | ✅ **ANSWERED 2026-09-02T17:17:39 — and it sat here reading OPEN for three days.** `tv/.human_eyes.jsonl` row 13 carries the observation: *"#foot-ver reads 'Millenium v442', title 'click - the state of this console' — ONE line, 33 chars, rect 145x16, visualLines 1"*, and the click opens `#ver-xref`. The brief was answered, the answer was banked, and nothing moved the row — **the ledger and the list were never joined**. [[the-unjoined-end]] |
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
- ✅ **CF-3 ENGINES CORROBORATE — CLOSED 2026-09-05, AND IT IS NOT A DEFECT.** The row asked for
  two names instead of a delta, and here they are: **`sweep would find`** and
  **`the other doctors`**. They are `console_doctor.SLOW`, and **34 vs 32 is the designed SPLIT,
  not a loss** — a cheap pass (`include_slow=False`) correctly omits them, so 32 is the whole
  roster it runs. Both ARE on the 34-roster; nothing is missing. `corroborate.py:723` already
  grades this per pass — cheap expects 32, full expects 34, and an **UNLABELLED** pass is UNKNOWN
  rather than assuming the full roster, which is what made it permanently red before. "Suspect the
  instrument first" was the right instruction and the instrument was already fixed.
- ✅ **CF-12 TWO CHECKS THAT REACH NO DURABLE SURFACE — REFUTED 2026-09-05 by measurement.** The
  premise is false. `console_doctor._slow_path()` **exists**, was **0.2 h old** when read, holds
  **both** rows — `sweep would find` state=ok (*"25 of 40 reel(s) show a stash panel"*) and
  `the other doctors` state=ok (*"vault 6 green / 0 needs-you · chronicle 10 green / 0
  needs-you"*) — and `slow_surface()` **is consumed**, at `control_app.py:15563` as `slowRows`.
  ⚠ Both read `unmeasured` in `report()` and that is CORRECT, not the defect: `report()` is the
  cheap roster view and the SLOW states live in the sidecar. Two surfaces, two questions.
- ◻ **CF-4 CONSOLE UI FAULTS** — 3 self-heals in 24h; page beating while blank (11,817 elements vs
  a high-water 84,541). ⚠ the self-heal converts a reproducible bug into an intermittent one —
  capture the pre-rescue state BEFORE healing.
- ◻ **CF-5 PROGRESS NUMBER** — two worlds claim him: `77f64154` 290 uniques vs `c5c2c92d` 280,
  4.6 days apart, both sets=120. ⚠ HIS TICKS ARE TESTIMONY — do not resolve in code by preferring
  the newer; that is already the behaviour being warned about. Route to truth is a GB-L brief.
- ◻ **CF-6 GUEST-WORLD GROWTH** — ⚠⚠ **RE-MEASURED 2026-09-05, AND THE DOOR IS ALREADY SHUT.**
  This row said *"~150 routes, ~148 probe artifacts, unbounded and unpruned"* and prescribed
  *"stop recording at the door"*. **That guard already exists** — `control_app.py:1506`,
  `if _haves and max(_haves) == 0 and not _seen: return False` — and it works. All-zero route
  writes per day: **08-29:69 · 08-30:34 · 08-31:11 · 09-01:38 · 09-02:243 · 09-03:3 · 09-04:0 ·
  09-05:0**. The newest all-zero write is **2026-09-03 05:23, 52.5 hours ago.** The pile stopped.
  ⚠ **I FIRST REPORTED IT "STILL GROWING THIS MORNING" AND THAT WAS WRONG TWICE OVER.** I read the
  FILE's mtime as growth — it moves on every write, including the two REAL worlds updating their
  own counts, and the only route written today is `77f64154` with 121/293/99, which is his actual
  board. Then my first count said **13 routes**: I had counted TOP-LEVEL keys instead of
  `byRoute`. Founding rule 4 — the instrument was mine, twice.
  **SO THE REMAINING WORK IS NOT THE DOOR. It is a one-time prune of 402 historical rows**
  (304 KB), and the code argues against doing that blind in its own words: *"a brand-new real board
  also posts zeros before the first tick, and that is indistinguishable from a probe once the row
  exists."* AGE does separate them — all-zero AND untouched 52 h+ AND predating the guard — but
  this is HIS board data, so it is measured and proposed, **not executed**. ⚠ One row carries a
  `01-01` stamp, which is not a real date; an age-keyed prune must handle it rather than treat it
  as ancient.
- ✅ **CF-7 FOOTAGE HAS A REEL — CLOSED 2026-09-05 AS A DUPLICATE OF B-82, WHICH IS ALREADY CLOSED
  SEVENTY LINES ABOVE IT.** Re-measured rather than assumed: `orphan_fold.plan()` answers
  `1 cluster · 1 frame · 195,266 bytes · **0 foldable, 1 REFUSED** for overlapping an existing
  reel`. B-82's row records the identical finding and the reason it must stay refused — *folding
  it would mint a second session id for one recording*, forging the independence the keep-gate
  demands. **The refusal is the correct behaviour, not the outstanding work**, so this row was
  never a task; it was B-82 wearing a CF number. ⚠ Its one live number belongs to CF-6, not here:
  the same report counts **591 probe artifacts** in the frame pool, which is the guest-world pile
  under a different name.
- ◻ **CF-8 BOARD IS CLAIMED = UNKNOWN** — correct as written, do NOT turn it into a number. Worth
  doing: surface the 110-of-110 same-world agreement as EVIDENCE for CF-5, and carry the last
  known answer WITH ITS AGE instead of a bare UNKNOWN.
- ✅ **CF-9 THE GATE'S VIEWPORTS** — render_check rendered four heights, all taller than his
  660px window. Fixed v2406 (his real 1120x628 + a pre-scroll reachability probe). ⚠ STILL OPEN:
  the fixture lays out differently from the live app (taskforce y=224/h=30 in the gate vs
  y=1050/h=502 live), so that gate cannot cover layout-in-situ and must not claim to.

---

# ✅ LANDED — the recent ships, read off the STAMP rather than the commit message


> ⚠ **THE FIRST VERSION OF THIS SECTION WAS BUILT FROM COMMIT SUBJECTS AND WAS BLIND TO THE
> SHIPS THAT MATTER MOST.** The repo's rule is *"a vNNNN label means the four stamps MOVED"*, so
> reading subjects looks equivalent. It is not: **a stamp can move under a `fix:` subject, and
> several did.** `96a4eafb` carries `"ver": "v2666"` while its subject reads *"fix: the shelf
> door reported success…"* — CI called that run v2666 and `git log --grep` cannot find it at all.
> A range subject (`v2650-v2651 — …`) hides its second version the same way.
>
> Rebuilt by reading `tv/WINDOWS_SHIP.json`'s `ver` field through `git log -p` — one of the four
> stamps `bump_version.py` writes, so a change to it **is** the ship by the repo's own definition.
> The subject-based pass missed **v2667, v2665, v2664, v2663, v2661 and v2660**, every one of
> them a `fix:`-subject ship. [[feedback-verify-not-proxy]] [[feedback-suspect-the-instrument]]
>
> `tv/test_tasks_ships_are_recorded.py` goes RED when one of the newest 12 is missing here, and
> also when this file names a version no stamp ever reached. The drift was caught by hand three
> times before it was given a gate.
>
> **THE WORKFLOW IT ENFORCES: bump → record the row here → commit.** The gate fails on its own
> ship if that middle step is skipped — it did, on v2670, which is how this line came to exist.

| version | commit | commit subject |
|---|---|---|
| **v2723** | `(this commit)` | v2723 — an empty read does not raise so a torn bible.html was served as a normal 200 and the only watchers that could notice need the page javascript a zero byte document does not have |
| **v2722** | `(this commit)` | v2722 — four more distinct attacks and one live check against his real 31 seals took the new lock from locked to open on evidence rather than on repetition |
| **v2721** | `(this commit)` | v2721 — the gate between a seal and a deletion had no lock so seven real sabotages had nowhere honest to go; declared with its own bar and banked from a re-runnable harness |
| **v2720** | `(this commit)` | v2720 — seal_verdict existed since v2702 and was called by one reporter while both deciders asked the old binary question; joined with the strict predicate so examined empty releases and nothing was taken does not |
| **v2719** | `(this commit)` | v2719 — the render gate excused a scroller in its ancestor branch and not in its self branch so a designed scroll area read as clipped; instrument fixed and the declared floor removed not raised |
| **v2718** | `(this commit)` | v2718 — a seven day old grok error was printed as the present state of his second eye while fourteen reads succeeded that day; age now decides staleness and raw json never reaches the line |
| **v2717** | `(this commit)` | v2717 — v2714 unified nine sites in bible.html and never touched control_app where the fleet number is actually built; the fleet now publishes the chronicle pair and the corroborator watches the banked denominator |
| **v2716** | `(this commit)` | v2716 — 96 terrorized was an unnamed literal printed as if the zone produced it; it is a game constant now named once and rendered from one source |
| **v2715** | `(this commit)` | v2715 — recording a ship in TASKS.md was a step somebody had to remember and it failed on v2670 v2712 v2713 and v2714; the bump writes the row itself now |
| **v2714** | `d2e8bc88` | v2714 — REG-684: HIS ruling, *"this needs a unified and sharing logic"*. The chronicle denominator was re-derived at ELEVEN sites and they disagreed on his own screen — `/api/fleet` returned 169/398 and 292/403 six minutes apart on the SAME board while the meter read 258/403. Nine sites now call one function; `_darkN`/`_uniLeft` keep both totals apart on purpose |
| **v2713** | `e6a484a6` | v2713 — REG-682/683: nothing in the repo ever asked whether a page scrolls sideways (zero coverage, now a metric on every target, proven both halves). And the known-but-unwatched dash overrun was recorded as 9px since v2609 — re-measured at **74px**, wrong by 8x |
| **v2712** | `daaaf719` | v2712 — REG-681: every ship left his 6 MB bible.html at ZERO BYTES for 4.8% of concurrent reads. `bump_version` wrote all four stamps with a call that truncates on open, and his console re-reads that file per request — his "panel that renders NOTHING". Now tmp + os.replace |
| **v2711** | `(this commit)` | v2711 — REG-680: his symmetric-pills ruling shipped at v2686 with nothing pinning it; now gated on the law, not the string |
| **v2710** | `(this commit)` | v2710 — REG-679: a change to render_check.py did not re-run the render gate, so I shipped a RED target through the hole |
| **v2709** | `(this commit)` | v2709 — REG-678: the template station names which Chronicle page a reel showed; the ledger was in the visit row all along, and the gate is synthetic because his shelf cannot exercise it |
| **v2708** | `(this commit)` | v2708 — REG-677: the console reported three versions and all three read the working tree; liveVer now names what actually shipped, with the age of the ref beside it |
| **v2707** | `(this commit)` | v2707 — REG-674: the UNDO button could hand a claimed browser the seed ledger and re-create the Dean defect |
| **v2706** | `(this commit)` | v2706 — REG-673: the un-seed snapshot was shared across profiles and never spent, so an Undo after switching profiles would clobber the other account |
| **v2705** | `(this commit)` | v2705 — REG-672: the tombstone gate says it cannot measure on a runner with no reels, via run_gates own skip_ok, instead of failing there forever |
| **v2704** | `(this commit)` | v2704 — REG-671: five defects a second review found in the first review's fixes, including a skip recorded as a pass and my denominator fix having the defect it fixed |
| **v2703** | `(this commit)` | v2703 — REG-670: three heart invariants read absent evidence as a positive claim; one passed vacuously on every machine but his |
| **v2702** | `(this commit)` | v2702 — REG-669: the evidence contract learns to say EMPTY; 22 of his 30 seals cover ZERO rows and say so, and the real defect is six seals over 42 rows |
| **v2701** | `(this commit)` | v2701 — REG-668: clipped is counted over descendants, not the node list, so my v2697 sweep printed `clipped 54/8`; a wrong denominator is worse than none |
| **v2700** | `(this commit)` | v2700 — REG-667: my v2696 copy rewrite grew the claim bar 27% and it covered the inbox popover close button at 375px; same promise, fewer characters |
| **v2699** | `(this commit)` | v2699 — the un-seed can be undone and names the ledger BEFORE it deletes anything; REG-666, four defects a code review found in one destructive control |
| **v2698** | `(this commit)` | v2698 — the automated world can play the stranger again: v2694 made it the owner so seed specs would pass, which made the claim bar unreachable and killed the one spec about the stranger path |
| **v2697** | `(this commit)` | v2697 — the search hint fits the phone box: a 70-char placeholder written for 1440 cut mid-word at 375; and every render count now carries its denominator, because `covered 0` hid a real overlap |
| **v2696** | `(this commit)` | v2696 — the claim button no longer promises another man's data; the heart flags a world reporting 0 while holding a ledger |
| **v2695** | `(this commit)` | v2695 — the heart now flags a stranger posting owner-namespace numbers; and the un-seed removes the inherited chronicle without wiping his own finds |
| **v2694** | `(this commit)` | v2694 — the automated world names itself the seed ledger; and the two ledger parses fail independently again |
| **v2693** | `(this commit)` | v2693 — a retro-sweep row says so; `completedTs` meant two things and nothing on the row said which |
| **v2692** | `(this commit)` | v2692 — the chronicle seed now names the LEDGER it belongs to; a claimed browser no longer inherits Konyo's 245 finds |
| **v2691** | `(this commit)` | v2691 — his sunder ruling, done on the TALLY not the roster: 12 chronicle rows → 6, found unchanged at 248 |
| **v2690** | `(this commit)` | v2690 — the vault door never opened for a NEW find: `_mayVault` was assigned in one branch and read in the other |
| **v2689** | `(this commit)` | v2689 — laneLocked could never populate; the found-bar went dark for every set piece; an open no longer restamps unmeasured facts |
| **v2688** | `(this commit)` | v2688 — REG-621: a grid floor of 330px on a 276px container put every remove button out of reach |
| **v2687** | `(this commit)` | v2687 — the entry stamp: the door travels with the reel, and onair/mini finally earn a denominator |
| **v2686** | `(this commit)` | v2686 — his two rulings: contrast to 4.86:1, and symmetric pills |
| **v2685** | `(this commit)` | v2685 — I broke one of his rulings implementing a later one; reverted |
| **v2681** | `(this commit)` | v2681 — the vault knows all three sunder forms; the chronicle keeps one row each |
| **v2680** | `(this commit)` | v2680 — six sunders one row each, settled from the game file; and one `_norm` |
| **v2679** | `(this commit)` | v2679 — the ships gate covered nothing on the only venue that runs it |
| **v2678** | `(this commit)` | v2678 — the absolute 280 was never reachable, so the law became a comparison |
| **v2677** | `(this commit)` | v2677 — a floor over an undefined world is not a floor |
| **v2676** | `(this commit)` | v2676 — synced: one conversion for the hunt hours, one naming rule for the ledgers |
| **v2675** | `(this commit)` | v2675 — a Chronicle screenshot proves he FOUND it, never WHERE it is |
| **v2674** | `(this commit)` | v2674 — one rename broke nine specs, and two "regressions" were the product improving |
| **v2673** | `(this commit)` | v2673 — my own fix left the literal it was supposed to remove |
| **v2672** | `(this commit)` | v2672 — four stale assertions, and one of them was the code being right |
| **v2671** | `(this commit)` | v2671 — eleven spec clicks aimed at a button hidden on purpose |
| **v2670** | `afc93f2d` | v2670 — six ships were invisible to every audit that reads commit messages |
| **v2669** | `e3e5d6fd` | v2669 — the census counted the dark cases without ever asking why |
| **v2668** | `af1b7a62` | v2668 — a gate passed while covering nothing, and the census had no denominator |
| **v2667** | `a7b87cf0` | fix: I fixed one call site and called the class done — plus the guard BUGS.md already cl ⚠ `fix:` subject |
| **v2666** | `96a4eafb` | fix: the shelf door reported success on the one failure he could see — and the coverage  ⚠ `fix:` subject |
| **v2665** | `1bbbc2fd` | fix: a floor is not a priority — the vault name absorbed 62% of every deficit ⚠ `fix:` subject |
| **v2664** | `c30a8ed0` | fix: seven of eight console tabs rendered at no width — a gate, green, and proven red ⚠ `fix:` subject |
| **v2663** | `e829ed7f` | fix: the wedge collisions were DISTANCE, not length — and --write-baseline lied about fa ⚠ `fix:` subject |
| **v2662** | `d5545649` | fix: a craft tooltip read an identifier that was never declared, and Routine I has been  ⚠ `fix:` subject |
| **v2661** | `57ae547f` | fix: the hardening advice counted attempts while the bar counted attacks ⚠ `fix:` subject |
| **v2660** | `f6a5260e` | fix: the ruling was enforced in the decision and contradicted by every number on screen ⚠ `fix:` subject |
| **v2658** | `3db06205` | v2658 — the red that gated nothing, and a gate whose message and exit code disagreed |
| **v2657** | `e9a56fef` | v2657 — one row missing a key hid a dead column for ever |
| **v2656** | `ec550e01` | v2656 — a review of my own ship found the claim was larger than the evidence |
| **v2655** | `af8beac9` | v2655 — the detector could not read the file it was about to watch |
| **v2654** | `552d3c1d` | v2654 — a dead field that was the denominator of his own question |
| **v2653** | `e68d927d` | v2653 — a footer that said "none of it us" about a number nobody measured |
| **v2652** | `eee4a6d5` | v2652 — a gate that decided by sniffing a character |
| **v2651** | `34532602` | v2650-v2651 — a retraction that vanished, and a new instrument that found an old backlog |
| **v2649** | `e904f8da` | v2649 — a reading aid three functions from dying |
| **v2648** | `aa57fa55` | v2648 — three holes a cold eye found, and all three were mine |
| **v2647** | `32274b28` | v2647 — the sabotage that could not fail |
| **v2646** | `33c69a1f` | v2646 — the tested encoder is not the used encoder |
| **v2645** | `c62fb53a` | v2645 — a seventy-character window that invented a finding |
| **v2644** | `e315cd3d` | v2644 — a fix that was one third applied, and the guard that could not see its own scar |
| **v2643** | `7894af0a` | v2642-v2643 — freed megabytes nobody freed, and the alarm that blinded the watchdog |

---
# 🎯 THE TRUE REMAINING SET — deduplicated 2026-09-05

> **Read this, not the historical tables above.** Everything above is kept as evidence; this is what
> is actually left. Produced by a read-only pass over all 1,215 lines cross-checked against 400
> commits, then re-measured by hand where a number mattered.

## ⚠ FIRST — 8 CLUSTERS WHERE MANY IDS ARE ONE PIECE OF WORK

The list looked far longer than it is because one decision wears seven names.

| the ONE item | ids carrying it | the proof they are one thing |
|---|---|---|
| **Define *clean* per reel** | **A15 · A4 · A7 · A8 · A9 · 146 · A20** | A9: *"folded into the PRINTER ZONE with A4·A7·A8·A15"* (his call) · A4 REMAINING = *"A15's clean definition"* · A15: *"AND IT GATES THE PRUNE. See task 146"* · A20 prerequisite = *"the printer/river itself (A4·A15)"*. **Seven ids, one ruling from him.** |
| **A ledger entry carrying its own proof** | **A14 req.2-4 · 166 · 133** | A14: *"the same one blocking 166"* / *"Closes the hole under tasks 133 and 166"*; 133: *"Answered by 166's ledger ruling"* |
| **Paid reads on the 29 unread reels** | **155 · 154-remainder · 146** | §💵: *"This unblocks 155, and therefore 154's remainder and 146"* |
| **Hover ground truth (cell → point → item)** | **181/HE-1 · 184/HE-4 · GB-L-1 · A18 · `miniauto.run`'s HARDENED gap** | GB-L-1 IS *"HE-1 look"*; A18 explicitly *replaces* the route 181/184 take |
| **The eye reaching a gate** | **165 · gh #186 · A13 · 182/185** | gh #186 is *"The eye's half of task 165"* |
| **Which world is his** | **CF-2 · CF-5 · CF-8** | CF-2: *"Same root as CF-8"*; CF-8: *"surface the agreement as EVIDENCE for CF-5"* |
| **Content-lost rows** | **136 · 148** | byte-identical prose since `a8016ea6` |
| **The heart umbrella** | **A16 ⊃ A1 · A2 · A3 · A11 · A13** | A16 declares itself the umbrella: *"all five are the heart reaching further"* |

## TIER 0 — FREE. No money, no ruling, no risk.

> ⚠ **THIS TABLE DRIFTED FROM THE PROSE ABOVE IT AND WAS WRONG ON 3 OF ITS 6 ROWS (2026-09-05).** CF-3 and CF-7 were already CLOSED in the prose while listed here as open, and CF-6's cell claimed *"still growing"* while its own prose row 62 lines up recorded the opposite, correction included. **The section advertised as the truth was the stale half** — which is the same defect the drift audit at the top of this file names for CF-1. When a row moves, move it in BOTH places.

| id | what | measured state | size |
|---|---|---|---|
| **CF-6** | Stop recording a board route at the door | ✅ **THE DOOR IS SHUT AND NOW PROVEN BOTH WAYS — 2026-09-05 17:28.** This cell used to read *"2.7× worse than filed … still growing while this is written"*, and **that was wrong**, contradicting CF-6's own prose row 62 lines above it. Re-measured: `byRoute` 404 (2 real / 402 zero-but-readable / **0 unreadable**), and the file is **byte-identical (304,226) between the 09:38 filing and 17:28 — eight hours, zero growth**. The only route stamped today is `77f64154` `pfx=''` with **[122,293,99]**: the OWNER world posting real counts. **A fresh `at` on an existing row is not a new row** — that misread is what "still growing" was. Newest GUEST (`I·`) route: **2026-09-03 05:23, 60.1 h ago; 0 in 48 h.** The guard landed **2026-09-02 23:47 (`4a367577`, v2454)**; 398 of 401 guests predate it and the 3 that followed all fall within 3.5 h, consistent with his console running the old code until its next restart. ⚠ **"0 new rows" reads identically to a guard nobody exercised**, so it was exercised against a TEMP file (his `board_tally.json` never opened for write): **RED** fresh guest posting zeros → `False`, 1→1 routes, nothing minted · **GREEN** fresh real world → `True`, admitted · **GREEN** already-banked world dropping to zero → `True`, no duplicate row, **and the drop written to `drops`**. That third case is the one that matters: it proves the guard is not simply refusing all zeros, so a real collapse is still recorded rather than silently healed. ⚠ The proof's FIRST run failed on **my own anchor** — I seeded the literal key `ownerkey` while `_route_key()` computes `owner|main` [[sabotage-is-usually-the-wrong-one]]. **REMAINING = HIS:** the 402 historical rows are his board data; removing them is the prune, and the prune is his call. | **S → done (his half open)** |
| **CF-5** | Two worlds claim him | **CORROBORATED BY CF-6's measurement** — the 2 non-zero routes ARE the `77f64154`/`c5c2c92d` pair CF-5 names. ⚠ HIS TICKS ARE TESTIMONY: route to a GB-L brief, never resolve in code by preferring the newer | **S** |
| **JOIN-3** | The 3 reels that are sealed AND names-read | **FREE by his own table** — names on disk, the seal does not carry them. Unblocks `ROUTED`, which is structurally unreachable for all 40 until it lands ⚠ figure carried from the 2026-09-04 measurement, not re-run | **S** |
| **CF-3** | Name the 2 missing checks (32 rows vs 34) | ✅ **ALREADY CLOSED — see the prose row ~86 lines above.** The two names are **`sweep would find`** and **`the other doctors`** (`console_doctor.SLOW`), and **34 vs 32 is the designed SPLIT, not a loss**: a cheap pass (`include_slow=False`) correctly omits them. Nothing is missing. Listed as open here only because this table drifted from the prose. | **closed** |
| **CF-7** | 1 orphan frame | ✅ **ALREADY CLOSED as a duplicate of B-82 — see the prose row above.** `orphan_fold.plan()` → *1 cluster · 1 frame · **0 foldable, 1 REFUSED*** for overlapping an existing reel, and **the refusal is the correct behaviour, not outstanding work** (folding it would mint a second session id for one recording). Never a task; B-82 wearing a CF number. | **closed** |
| **CF-8** | Carry the last-known answer WITH ITS AGE | `stale-reading` shape. Do NOT turn UNKNOWN into a number | **S** |

## TIER 1 — HIS, AND EACH ONE UNBLOCKS A CLUSTER

| id | the question | why only he can answer |
|---|---|---|
| **A15-CLEAN** *(unblocks 7 ids)* | Which door decides *clean* per reel? | **12 of 40 finished by the REEL door, 0 by the FRAME contract, 0 by both.** Conjoining them is the collapse v2312 attempted and v2314 withdrew. It gates the prune |
| **BARS** ⚠ **NEW — was absent from this file entirely** | Do the locks' bars read `wilson` or `wilsonByAttack`? | v2656 (`ec550e01`): `prune.arm` 0.9259 vs **byAttack 0.5655** against a 0.839 bar; `vault.sweep_start` 0.8064 vs **byAttack 0.3424** against 0.510. The guard is *"explicitly forbidden from settling it"*. **This decides the deleter and the money door** |
| **PRUNE-LIVE** | Is re-running existing axes against a live process an INDEPENDENT look? | `prune.arm` needs a third kind; it is the one door with no undo. **DO-NOT-BUILD is an honest outcome** |
| **136 · 148** | One sentence each, or they are permanently unactionable | Content lost since the earliest tracked version. Nobody can act, including him |
| **GB-L-5/6/7** | Three briefs asked and never answered | Only he can look. ⚠ **RE-MEASURED 2026-09-05 by the `human-eyes` gate itself, not carried forward: GB-L-7 81.5 h · GB-L-6 94.3 h · GB-L-5 94.4 h** — 8 briefs recorded, 2 answered with a LOOK, **3 still owed**. The gate is RED on his Mac for exactly this, and CI can never see it, because the only automated venue is the one venue that cannot run it. *"A question nobody answered must not fade into silence."* |

## TIER 2 — REAL BUILD, NO MONEY

| id | what | state |
|---|---|---|
| **GATE-EYE-2** | The 375px clipping backlog | **54 clipped @375 · 5 @901 · 1 @wide.** Instrument fixed v2650-51; the defects are untouched |
| **A17** | Editorial redesign | in progress; 9 confirmed defects, no closing commit. Overlaps GATE-EYE-2 |
| **A5** | Widen the walk to the 28% of rows that nest differently | the 72% half shipped v2578 |
| **A13** | Live-console contradiction check reaches a blocker | half shipped (v2404/v2511); the live half filed, not faked |
| **gh #186** | Contract for what an eye may be asked to photograph | OPEN; 165's other half |
| **A14 req.2-4** *(= 166 = 133)* | Ledger entry carries re-verifiable proof | **blocker is real and measured**: `d2r_foundLog` is 412 rows of display strings with no reel/frame/witness, and 8 of 169 owned items have no row. Deferred by his ruling |

## TIER 3 — SPENDS MONEY, BEHIND THE PROOF

**155 → 154 → 146.** Paid reads on the **29 of 40 never-read reels**. ⚠ Do NOT sweep all 40: 24
return nothing new. Sequenced AFTER A15-CLEAN, per his own condition — *working · coded · not
looped · debugged*.

## TIER 4 — LAST, BY HIS EXPLICIT ORDER

**A18 / MINI AUTO** (the rebuild, not v2621's recorder) and **A20** (the river, visible). Both
⏸ HIBERNATING and DEFERRED, not dropped: *"we will get to that after we completely finish every
tasked list and grok's handoffs in between too."*

## ⬜ WHAT COULD NOT BE SETTLED — UNKNOWN, and not carried forward as fact

- ✅ **SETTLED 2026-09-05 — `run_gates.py` IS green at HEAD, on CI, and the honest verdict is not
  the word "green".** Run `33970973928` on `96a4eafb` (v2666), workflow *📺 TV DIABLO — agent tests*,
  step **`THE GATE SET (tv/run_gates.py)` = success**. Its own closing lines, quoted:
  **`✅ 138 gate(s) passed, 4 skipped for a DECLARED reason.`** and
  **`⚠ 78 CASE(S) DID NOT RUN inside those gates`** — `test_control=26`, `test_chronicle_template=12`,
  `test_inventory_lattice=11`, `test_stash_eye_aspect=8`, `test_chronicle_calibrate=4`, +11 more.
  The 4 skips are the HOST_FIXTURE shape and each declares itself: `reel_demo` (his shelf absent →
  *3 check(s) UNKNOWN*), `overlap_ratchet` (**baseline measured on Darwin, run on Linux** — font
  rasterisation, so the comparison is void, not passing), `human-eyes` (*"not a pass"*), `live-panel`
  (nothing listening on `127.0.0.1:17772`). **SKIP ≠ PASS, and the gate set says so itself.**
  ⚠ **AND THE 78 IS NOT ACTIONABLE, WHICH IS CF-3'S OWN PRINCIPLE LEFT UNAPPLIED ONE LEVEL DOWN.**
  `run_gates.py:2264` parses `skipped=(\d+)` out of each gate's detail and reports **suite + count,
  never the case names or the reasons** — exactly the *"a delta of 2 is not actionable, two names
  are"* complaint, one layer lower. Denominator: those 16 suites hold **2,783 tests**, so 78 is 2.8%.
  Of the reasons written at the 165 `skipTest(` call sites, several **cannot be true on a runner** —
  *"bible.html is not on this machine"* (28 sites) and *"node is not installed"* (7) are both false
  on CI, where bible.html is tracked and node runs the intake smoke in the very next step. So the
  78 is **not yet explained**, only counted. NEXT: make the counter carry aggregated reasons.
- **A11's 30/11/8 census** and **A2's per-lock wilson figures** at HEAD — both need the instruments run.
- **The 40-reel shelf figures** (29 unread / 12 / 12 / 3 JOIN) — carried from 2026-09-04, not re-measured.

---

## ✅ SHIPPED 2026-09-05 — v2656 · v2657 · v2658 · fix: (`origin/main` af8beac9 → a50c925c)

**Confirmed three ways, not one**, because `git push | tail` reports tail's status and that is how
a refused push once read as a success: `GIT_EXIT=0` · the ref line `af8beac9..a50c925c main -> main`
· `git rev-parse origin/main` = `a50c925c`, 0 ahead.

**The gate's own verdict, quoted:** second eye ✅ · visual-lock ✅ · boss portraits ✅ ·
**tv suites green** ✅ · *"the page was rendered and looked at"* ✅ · **Playwright smoke GREEN** ✅ ·
deployable change, CI publishes. ⚠ Console demos **SKIPPED** — `control_ui.html` unchanged for 6
commits. That is a declared skip and is recorded as one, never as a pass.

### THE CI PICTURE THAT MADE THIS URGENT — and my first statement about it was a sample, not a verdict

I reported *"CI red for four consecutive pushes."* That was the last four runs I happened to list.
**Measured over 150 runs: TV DIABLO is 149 RED of 150, across three days** (one green,
`f215cf5b`). **Routine I has not been green since 2026-08-29** — 344 non-green, 141 of them
*cancelled*, and a workflow routinely cancelled is a workflow nobody waits for.
`test_control`'s failing case was **born red** in v2431 and never passed once.

⚠⚠ **AND NOTHING GATED ON ANY OF IT.** At every one of those SHAs *"Publish — gates, review, then
deploy"* is **success**, because `publish.yml` needs only its own in-workflow jobs — not
`tv-tests`, not `routine-i`, not `routine-m`. **The site published throughout.** A gate that is
always red and one that is always green are the same defect; these had stopped carrying
information.

### CI DELTA ON THE SHIPPED SHA — read against the 149-red baseline, never against state

| workflow | before | on `a50c925c` |
|---|---|---|
| **Routine M — swallowed-exception ratchet** | failure | **success** |
| Routine G · H · J · K · L | success | success |
| 📺 TV DIABLO — agent tests | failure, **16 gates** | failure, **3 gates** |
| Routine I — Playwright suite | failure (7 days) | *still running at the time of writing* |

⚠ **Routine M green is the first EXTERNAL confirmation** — the swallow ratchet is back at its 74
baseline on a machine that is not his.

### 🎯 THE MEASUREMENT: 16 RED GATES → 3

```
BEFORE af8beac9 (16): test_control · test_scope_reach_signal · test_board_tally_alarm ·
                      test_render_coverage · reel_demo · test_reel_retention · swallow_ratchet ·
                      test_printer · test_probe_unknown_law · test_dead_field · test_one_funnel ·
                      test_printer_reach · test_board_story · overlap_ratchet ·
                      test_heart_surface · test_cf_handoff
AFTER  a50c925c (3):  test_dead_field_reads_jsonl · test_printer_reach · test_board_story
```

⚠⚠ **AND I UNDER-BRIEFED THE FLEET, WHICH IS WHY TWO OF THE THREE ARE STILL RED.** The brief said
"16 gates"; the job list held **9**, and I took 5 myself. **`test_printer_reach` and
`test_board_story` were never assigned to anyone** — they are red because nobody looked at them,
not because they resisted a fix. Naming that here because a count that does not match its own list
is exactly the shape this file exists to catch.

### ⚠⚠ A REVIEW OF THE PUSHED BYTES FOUND FOUR DEFECTS IN THE SHIP ITSELF

| what | why it matters |
|---|---|
| `test_dead_field_reads_jsonl` read the **gitignored** live tombstone store | a **NEW red gate**, introduced by the commit whose subject was *"the last red gate"*. Fixture-fed now; verified OK in a reproduced CI venue |
| `reel_router` blanked its own `seen_why` **one line after writing it** | `rep.update(..., "why": "")` re-collapsed *"survey unreadable"* into *"no survey time"* — the exact thing the change was written to prevent. [[the-unjoined-end]] |
| `reel_demo` exited **0 / PASS** having walked **nothing** | a false red traded for a **false green**, which is the worse half: a red gets investigated, a green ships. Now exit 77 with a **narrow** declared skip — a shelf that EXISTS and walks nothing still fails |
| `run_gates` stdout-first hid `FAILED (failures=N)` | unittest writes its verdict to **stderr**. **Grok and the code review reached this independently**, from different directions — that agreement is why it was taken rather than argued. stdout only for SKIP; both streams for FAIL |

⚠ **AND MY OWN VERIFICATION WAS WRONG ONCE.** I reproduced the CI venue with `git archive HEAD` —
which exports the last **COMMIT**, while the fixes were uncommitted. I graded the old bytes. Redone
with the working tree overlaid, `reel_demo` immediately exposed a **second** defect: an earlier
`return 1` made the new `return 77` unreachable, so it printed *"declared SKIP"* and exited 1
anyway. **Two return paths, one patched.** Founding rule 4, on my own instrument.

---

# ✅✅ CI IS GREEN — `cd5be969`, 2026-09-05

**📺 TV DIABLO — agent tests → SUCCESS.** Read by DELTA, never by state: it is the **only success
in the visible window**, against a measured baseline of **149 RED OF 150 runs across three days**.
`Routine M` ✅ and `Publish` ✅ beside it — three of three settled workflows green.

```
07:36  success  cd5be96   <- the ship
07:06  failure  a50c925
05:15  failure  af8beac
04:29  failure  e68d927
03:49  failure  3453260
```

### THE PATH: 16 RED GATES → 3 → 0

| what it was | count |
|---|---|
| REAL regressions | **2** — `render_check.py:332`'s non-raw `\d` displacing a gate's declared skip reason on CI's 3.12 while invisible on his 3.9; and the swallow ratchet 74→76, two new files handing a failed read back as `[]` and `{}` |
| stale assertions | 4 |
| missing CI dependency | 1 — `websocket-client`, whose absence failed a gate that looks unrelated to sockets |
| host-fixture gates | 6 — the runner has none of his footage |
| message/exit-code contradiction | 1 — `overlap_ratchet` printed `⚪ UNKNOWN` and exited FAIL, so a browserless runner counted it red while nine `⚪ SKIPPED` siblings were not |
| **structurally unsatisfiable** | 1 pair — `test_scope_reach_signal` carried a test forbidding its own registration while `TestNoOrphanSuite` REQUIRES it. No edit to either side could satisfy both |
| **never assigned to anyone** | 2 — `test_printer_reach`, `test_board_story`. My brief said "16 gates"; the job list held nine and I took five |
| found by reviewing the PUSHED bytes | 4 more, in the ship itself — including a **new red gate introduced by the commit titled "the last red gate"** |

### ⚠ WHAT THIS COST IN SELF-INFLICTED ERROR, recorded because the count is the point

**Five measurements of mine were wrong and each was caught by re-checking, not by the check:**
"CI red for four pushes" (a sample reported as a verdict — it was 149/150) · `board_tally` at 13
routes (I counted top-level keys, not `byRoute` — it is 404) · "the artifacts are still growing"
(the file's mtime moves when his REAL worlds write; the pile stopped 52 h earlier) · grading
uncommitted bytes with `git archive HEAD` · and a grep that reported a skip which did not exist,
because a docstring **arguing against** a `skipUnless` contains the word.

**And THREE sandbox escapes, every one of which made a check PASS:** my CI-venue recipe reading his
live `TASKS.md` through `board_sync.py:40`'s literal default · that same recipe grading the previous
commit · and a corpus whose own comment calls it *"built rather than borrowed"* silently reading his
real **30 seals** (a runner reads 0). **A sandbox is not a sandbox until you ask it what it
resolves to.** An AST sweep of every module-level assignment in `tv/*.py` finds exactly **one**
string constant starting with `/Users/` — `board_sync.py:40` — so that escape class has a
population of one, and it is handled at the test level now.

⚠ **`Routine I` (Playwright) is NOT part of this.** It is a separate 7-day red — last green
2026-08-29, 344 non-green runs, 141 of them *cancelled* — whose failures cluster **by shard, not by
cause**, and whose shard-5 count is unmeasurable because the 700 KB log truncates before its
summary. It is last by its own breadth, and nothing here claims to have touched it.

---

## ⛔ JOIN — REFUTED 2026-09-05. It is not free work, and it is not his call either.

This file (and my own board row) carried it as **"the cheapest work on the shelf, and it costs
zero — the names are on disk and the seal does not carry them."** He asked the right question:
*"whats wrong with that? writes to my real store in what way in what meaning context"* — and the
honest answer was a measurement, not a hedge. I had said *"your call"*, which was lazy: it was
answerable, and the answer is that **nobody should do it.**

**WHAT THE WRITE IS.** Adding `extracted: [name, location, provenance]` to 4 seals — four tiny
edits in a 9,713-byte file.

**WHAT IT DOES.** That field is read by `frame_authority.seal_covers_extraction`, which is called
inside **`frame_verdict` — *"MAY this one frame be deleted?"*** Simulated in memory, nothing
written: all four flip `False → True`, moving **345 FRAMES from HELD to DELETABLE.**

| reel | frames |
|---|---|
| `reel_s_1784984019250_95276` | 154 |
| `reel_s_1785078127173_28278` | 115 |
| `reel_s_1787242455315_9654` | 8 |
| `reel_s_1787512325134_62795` | 68 |

**WHY IT IS WRONG, NOT MERELY RISKY** — the contract's three facts against his real banked rows:

| fact | the contract's own words | his data |
|---|---|---|
| `name` | *the item's name, which only ever appears in a hover tooltip* | ✅ `"Chaotic Grand Charm"` |
| `location` | *WHERE it was — the container **AND THE CELL BOX INSIDE IT** (his slot identity)* | ⚠ container `lane: "stash"` present; **CELL BOX ABSENT** |
| `provenance` | *where it was SEEN — which reel and which frame* | ✅ `witnesses: [{session, frame, conf}]` |

Measured: every banked row in `vault_accum.json` carries **exactly** `conf · count · kind · lane ·
lastSeenTs · name · witnesses`. **Nothing cell-, slot- or box-shaped exists anywhere in it.**

Two of three facts are genuinely on disk. `location` is not, because the old sweep recorded the
**container** and never the **slot**. Writing the full contract asserts a fact nobody measured and
makes 345 frames disposable on an invented claim — precisely what the contract's own comment
forbids: *"an unstated fact is an unextracted one; 'the sweep probably got it' is not a record."*

⚠⚠ **SO THIS IS THE SAME WALL AS A5 AND REG-340 — slot identity was never captured. It is a
CAPTURE change, not a code change, and re-sealing cannot close it.**

⚠ The only version that could ever ship is a PARTIAL backfill — `extracted: ["name",
"provenance"]` — which is honest, still fails the contract, and therefore still **holds** all 345
frames. That is the correct outcome, not a workaround.

**⚠ AND TWO OF MY OWN CLAIMS ARE RETRACTED HERE:** *"4 reels, and it costs zero"* (it is neither
free nor a missing label) and *"it writes to his seal store, so it is his call"* (it was mine to
measure, and the measurement removes the decision).

---

## ✅ LIVE-FILE GUARD — closed 2026-09-05, and the row was wrong in BOTH directions

The row read: *"conftest's `live_data_is_not_collateral` and `no_orphaned_children` are
`@pytest.fixture(autouse=True)` but there is NO pytest config anywhere and CI runs unittest +
run_gates.py. **NINE files** are guarded only by them."*

**Measured, and it is FIVE, not nine — and only FOUR are on disk.** `run_gates` already covered ten
of the fifteen `LIVE_FILES`, and covered them *better*, because it fingerprints **between gates** and
so can name WHICH gate wrote a file; a session-scoped fixture only ever sees the whole run.

**The four that really fell through were the ones with unusual NAMES, not unusual importance:**

| file | why the net missed it |
|---|---|
| `.console_scars.json` | `*.json` does not match a **dotfile** |
| `vault_accum.json.healer_bak` | a different **extension** entirely |
| `vault_seen.json.healer_bak` | ″ |
| `vault_swept.json.healer_bak` | ″ |

⚠ **Three of the four are the healer's only copies of the vault stores.** A backup a suite silently
overwrites is worse than a live file it overwrites, **because the backup is what the repair reads.**
Net widened to `*.json · *.jsonl · .*.json · *.healer_bak`: **14 of 15 covered**, the last being
`vault_ledger.json`, which is simply absent — and a CREATION is still caught, because the diff
unions both key sets rather than iterating the `before` snapshot.

### ⚠⚠ AND THE HALF THAT MATTERED HAD **ZERO** COVERAGE

`no_orphaned_children` is a `@pytest.fixture(scope="session", autouse=True)`. Measured: **no
`pytest.ini`, `setup.cfg`, `pyproject.toml` or `tox.ini` anywhere**; CI runs `python3
tv/run_gates.py`; and run_gates' only occurrence of the word `pytest` is `.pytest_cache` inside a
directory skip-list. `_descendants`, `leaked` and `reaped` each occurred **ZERO** times in it.

**So the guard written for *"a suite spawned something and never reaped it"* had never run once on
a gated path** — including on 2026-09-05, when that is exactly what happened: *"my pc is super hot
you left background processes running"*, the **fourth** such correction. The fixture's own docstring
records the original cost: a suite spawned `tv/tv_diablo.py`, it ran **22 minutes** past the suite,
writing stub reads into live `state.json` and spending **39 of a 240-a-day read cap**.

**Wired into `run_gates` now**, which is the only place it can work: every gate is its own
subprocess, so anything left behind is a descendant of the harness. It **IMPORTS** conftest's
walker rather than re-implementing it — two copies of a process rule, with a kill on the end, is
[[copy-drift]] at its most dangerous.

⚠ **IT REPORTS AND NEVER KILLS.** `pkill -f` is banned here and a descendant-walk from inside the
harness that spawned them is one bad ppid away from taking his console. **Naming is what was
missing**; killing belongs to `claude-owns sweep -f` and `reap -f`, which already refuse his ports
by name. ⚠ And an unreadable process table prints **UNKNOWN**, never a clean sweep — silence is not
evidence.

---

## ✅ BARS — CLOSED, AND IT WAS NEVER HIS CALL

**He asked the question that produced this:** *"what do you mean by me? should be done by the
locks?"* — and he was right on both halves.

**His ruling already existed**, 2026-09-04, in his own carved words:

> *"Beware n inflated by repetition. `printer.stream` banked 83/83 — but 80 of those were TWO
> attacks applied to 40 reels each. Five distinct attacks scores 0.5655, not 0.9558. Looping one
> attack over more inputs buys a bigger number and proves nothing new; **more KINDS is what earns
> HARDENED**."*

`self_arming` has **computed and published `wilsonByAttack` since REG-600** while `state` went on
being decided by raw `w`. So the repetition was **reported and never enforced** — a claim outrunning
its evidence, in the module built to stop exactly that.

**Enforced now. Measured effect — it moves the two doors that matter, and only three rows:**

| lock | was | wilson | byAttack | bar | now |
|---|---|---|---|---|---|
| **`prune.arm`** — the deleter, no undo | OPEN | 0.9259 | **0.5655** | 0.839 | **LOCKED** |
| `vault.apply` | HARDENED | 0.9259 | **0.4385** | 0.722 | **LOCKED** |
| **`vault.sweep_start`** — his money | OPEN | 0.8064 | **0.3424** | 0.510 | **LOCKED** |

**14 of 17 locks are unchanged**, so this is not a blanket demotion — it is three badges that were
resting on repetition.

⚠ **A BADGE, NOT A DOOR, which is why it did not need asking.** `may()` has **zero** production
callers (both greps are prose in comments) and `_PRUNE_SAFE_TO_RUN` is a separate switch that
**remains his**. What changed is what the board CLAIMS, not what anything does.
⚠ **An unbanked attack count does not silently fall back** — `deciding` / `decidingWhy` say out
loud that the badge rests on a figure whose repetition nobody measured.

### ⚠⚠ THE WIDER CORRECTION, and it is the more useful half

**Of SEVEN rows I had marked "HIS CALL", only ONE was genuinely his.**

| row | what I said | the truth |
|---|---|---|
| `bars` | his call | **his ruling already decided it** — mine to implement |
| `gh #210` | his call | he ruled *"YES most definitely BUT it needs to be coded"* — waits on the CHAIN |
| `155` | his money | **decided** 2026-09-04, conditionally — waits on the proof path |
| `166` | his call | he ruled; blocked on data the loggers never carried |
| `154` | his call | blocked on 155, which is blocked on proof |
| `JOIN` | his call | **refuted** — blocked on capture, never his |
| `CF-6` prune | his call | genuinely borderline, and the only one still arguable |

**"His call" must mean NO MEASUREMENT CAN SETTLE IT.** Using it for anything else is the escalation
scar wearing a politeness costume: *never escalate a question you have not first tried to measure* —
otherwise you make him answer the same thing twice.

---

## ✅ SHIPPED — `cd5be969 → be704dc7`, six fixes, 2026-09-05

Confirmed three ways because a piped `git push | tail` reports tail's status: `GIT_EXIT=0` · the
ref line `cd5be969..be704dc7  main -> main` · `git rev-parse origin/main`, 0 ahead.
Gate: **tv suites green**, and it DECLARED its two skips rather than hiding them — console demos
(control_ui.html unchanged for 15 commits) and smoke (no bible.html/spec changes).

| fix | what it was |
|---|---|
| **orphan guard** | a guard that had **never run** — a pytest `autouse` fixture in a repo with no pytest config, while CI runs `run_gates.py`. `_descendants`/`leaked`/`reaped` occurred **zero** times there. ⚠ And my FIRST CUT was blind by construction: it walked the process TREE, but `subprocess.run` waits for each gate, so a leaked child re-parents to launchd before the check looks. Now caught by IDENTITY. Proven both ways — names a real re-parented leak, silent on a clean run |
| **live-file net** | four files missed by NAME SHAPE, not importance: a dotfile `*.json` cannot match, and three `.healer_bak` — **the healer's only copies of the vault stores.** A backup a suite silently overwrites is worse than a live file, because the backup is what the repair reads |
| **the honest lock figure** | HIS 2026-09-04 ruling, enforced instead of reported. `prune.arm` (the deleter), `vault.apply` and `vault.sweep_start` (his money) were OPEN/HARDENED on raw `n` and would not open on `wilsonByAttack`. 14 of 17 locks unchanged |
| **cache shape** | `len(hit) == 3` refused the five-element superset — a defect that got **worse** the more the v2288 fix succeeded |
| **classifier version** | the FREE gate that decides whether a reel is EVER READ had no version, so a `panels: 0` verdict was **un-invalidatable**. 0 of his 437 rows back-filled |
| **the record** | of SEVEN rows marked HIS CALL, only ONE was |

### ⚠ AND THE INSTRUMENT FAULTS, because six in one session is the finding

Every one was mine, and every one was caught by re-checking rather than by the check itself:
a sample reported as a verdict (149/150, not "four pushes") · counting top-level keys instead of
`byRoute` (13, not 404) · reading a file's mtime as growth · grading uncommitted bytes with
`git archive HEAD` · `pgrep -f "time.sleep(300)"` searching for `time.sleep300` because parens are
a regex group · and reading `TARGETS` by AST, which skipped `os.path.join(...)` as a Call and
reported all twelve rendering the wrong file. **In every case the COUNT was the tell.**

---

## ✅ BOARDSYNC — CLOSED by naming ONE source, which is the only thing that ever closes it

Three surfaces describe the same work, and that is one too many. `copy-drift`'s first rule is not
"keep them in step" — it is **name one source; everything else is a build output.** If you cannot
say which in one sentence, that is the bug.

| surface | what it is now |
|---|---|
| **`~/.claude/tasks/session-bf4f066b/`** (the live count is in the viewer at :17955 — a number typed here is one that goes stale, and this table is the one place that must not) | **THE SOURCE.** His ruling, 2026-09-05: *"make it a defaulted way from now. i want this the way you update and progress and complete the tasks."* It is what he opens, on :17955, and it carries dependency edges (`blocks`/`blockedBy`) the other two cannot express |
| **`TASKS.md` — 1,659 lines** | **THE DURABLE ARCHIVE, and it keeps that job.** It exists because a list that lives in a session does not survive a restart — 993 turns once had to be recovered from a 688 MB transcript. It holds the EVIDENCE a board row cannot: the measurement, the refutation, the commit |
| **the D2R Console Manifest artifact** | **RETIRED as a work surface.** 225 row documents against its own `board/mirror` flag saying `count: 113` — it has already drifted, and nothing reconciles it |

**So the rule from today: the store is where a row's STATE lives; `TASKS.md` is where its EVIDENCE
lives; the artifact is not updated as work moves.** Two surfaces with different jobs is not
duplication — `TASKS.md` was never trying to be a live board, and the store was never trying to
hold a paragraph of proof. The artifact was trying to be both, and it is the one that drifted.

⚠ **This does not delete the artifact** — it is a real record of a real day and its rows carry
reasoning worth reading. It simply stops being a thing anyone has to keep in step, which is the
only honest way to have three copies of anything.

---

## ⚠ RETRACTION — I closed "CI has a browser now" and the fix was INERT

**Both surfaces said this was done. It was not, and the CI run said so in its own output.**

`e14c0fb5` was the first run with Chromium installed and cached — cache ✅, install ✅, deps ✅ —
and the gate still printed:

```
⚠ overlap_ratchet   0.1s   ⚪ UNKNOWN — headless chrome would not start, so no width was measured
```

**The 0.1s was the tell.** A real launch attempt cannot fail that fast.
`render_check.CHROME` was the literal string `/Applications/Google Chrome.app/…`, and
`_chrome_up()` asks `os.path.exists` of it — a path that **cannot exist on a Linux runner**. The
install was dead weight: CI minutes spent fetching a browser no reader could see.
[[the-unjoined-end]] — built at both ends, never joined — **in my own fix, one commit after
shipping it, and I had already marked the row closed.**

`CHROME` is resolved now, in the order `grok-second-eye` §2 already records for a second-eye
binary — env override, then KNOWN INSTALL LOCATIONS, never one hardcoded guess:

| | |
|---|---|
| 1 | `TV_CHROME` — an explicit override always wins |
| 2 | his Mac's Google Chrome |
| 3 | Playwright's cached chromium (`~/.cache/ms-playwright/chromium*/chrome-linux/chrome`) — CI's |
| 4 | `google-chrome` / `chromium-browser` / `chromium` / `chrome` on PATH |

⚠ **AND THE ROW STAYS OPEN, because finding a browser is not measuring.** The venue guard shipped
one commit earlier will now correctly refuse to grade Linux counts against a macOS baseline, as a
DECLARED skip. Turning that into a real measurement needs a **CI-blessed baseline**, which is its
own job and is not claimed here.

### The rule this adds to the day's list

**A fix is not verified by the steps that ran, but by the thing they were supposed to change.**
Three green install steps proved a browser was downloaded. They proved nothing about whether
anything could find it — and the gate's own one-line output said so, in a run I had already
declared a success.

## 🎛 THE 7 CONSOLE TABS ARE UNREACHABLE BY THE RENDER LANE — BY CONSTRUCTION

`tv/control_ui.html` carries **8 real tab elements** (`<button class="ht" data-tab=…>`): `crafts
forge fsets funi session tools tvd vault`. Exactly **one** of `render_check.TARGETS`' 12 entries
loads the console, and it never navigates — its `activate` is a *readiness predicate* asserting
`#btn-miniauto` is visible and not inside a collapsed `<details>`. Only the `vault` target
navigates at all, and it clicks the **board's** vault tab, not the console's.

**Why adding seven targets there would be decoration.** The console's tabs are a **shell router**,
not panels. `_shellLight()` stamps `body.dataset.shellTab`; `_shellRoute()` calls `switchTab()` on
a board **iframe** whose src is an absolute server path — `/board?app=1&engine=1&v=boot#session`
(`control_ui.html:18507`). `render_check` loads the console **from the filesystem**, so that iframe
resolves to `file:///board`, never loads, and `_shellRoute` returns false at
`if (!w || !w.document) return false;`. Seven targets added to that lane would refuse on every
single run — the same always-refusing shape that made the `cichrome` fix inert, one week apart.

**Where it does belong.** A lane that SERVES the console over http. Both halves already exist and
have never been joined:

| half | where it lives | what it lacks |
|---|---|---|
| a served console on a private port | `test_button_matrix.py` — boots its own `control_app` via `TV_CONTROL_PORT`, `--no-open`, stops it after | **no browser** — it is HTTP-only, it cannot click or see paint |
| a browser driving real pixels | `render_check.py` — CDP on :9224 | **no server** — it loads `file://`, so the board iframe is dead |

⚠ **It must never bind or kill `:17772` — that is his live console.**

**The class worth catching is v2125's, and the file records it in its own words:** a tab *lit* while
its destination stayed `display:none` at `height=0` — *"it scrolled to a hidden element and nothing
moved."* So the check must prove **the destination painted**, never that the button highlighted.
`_shellRoute` already models this correctly at v2120/#110: *"SUCCESS IS THE BOARD MOVING, NOT THE
FUNCTION EXISTING."*

**Status: open, and mine.** The finding is measured; the build is a new joined lane, not seven
lines in an existing one.

### ⚠ RETRACTION — I said those seven targets "would refuse on every single run". They do not.

I wrote above that adding console-tab targets to `render_check` would be decoration, because the
board iframe's src is the absolute path `/board?…` and the lane loads from the filesystem. The
first half is true. **The conclusion was wrong, and testing it took one script.**

`render_check` **already has a serve mode**, and most of its lane uses it: `page`, `state-panel`,
`heart`, `locks`, `advanced`, `advanced-shadow` and `advanced-fleet` all carry `"serve": True`,
which boots a private `control_app` on an ephemeral port (and refuses `:17772` **by name** — his
live console) and loads the target over http. The `console` target is simply one of the five that
does not. I read the one target I cared about and generalised from it.

**Measured, served, at 1440x1000** — clicking each `#head-tabs .ht[data-tab]` and reading the
board's own `.tab.active` through the iframe:

| tab | `body.dataset.shellTab` | board `.tab.active` | routed |
|---|---|---|---|
| session · forge · crafts · funi · fsets · tools · vault | matches | matches | ✅ 7 of 8 |
| tvd | `tvd` | unchanged | **correct — see below** |

`tvd` stamps the route and deliberately leaves the board alone. `control_ui.html:16139`:
`if (b.dataset.tab === 'tvd'){ document.body.removeAttribute('data-view'); shellHome(); return; }`
— *"TV·D = the cockpit home"*. I reproduced the non-routing three times with settle time and was
about to file it as the v2125 defect. It is the design, and the line says so in its own trailing
comment. **Read the comment before judging a measurement; ignore it when judging the code.**

**So the work is a flag, not a new lane.** Console-tab targets with `serve: True`, asserting
`shellTab == board .tab.active` for the seven routing tabs and cockpit-home behaviour for `tvd`.
The class worth catching is still v2125's — prove the DESTINATION moved, never that the button lit.

### `targets` — routing PROVEN, the gate NOT shipped, and why I backed it out

The console-tab render target was written, run at all five widths, and then **reverted**. What it
established stands; what it could not do cleanly was not shipped.

**Established (reproducible, served, 1440x1000):** clicking each `#head-tabs .ht[data-tab]` and
reading the board's own `.tab.active` through the iframe — **7 of 8 tabs route the board**
(`session forge crafts funi fsets tools vault`), each with `body.dataset.shellTab` agreeing.
`tvd` stamps and deliberately does not route: *"TV·D = the cockpit home"*
(`control_ui.html:16139`). Reproduced 3/3 with settle time.

**Why it is not in `TARGETS` yet.** The target needs a selector, and neither candidate gives an
honest verdict:

| `sel` | verdict | why it is wrong |
|---|---|---|
| `#head-tabs .ht` | 🔴 `imgs 5/8 broken` | contradicted by the pixels — the strip renders all 8 icons cleanly, and all 7 files exist on disk and serve **200 with real bytes** from the private console |
| `#tvd-eng` | 🔴 `painted but carries NO TEXT` | it is an `<iframe>`; its text is a separate document the parent-side probe cannot read |

⚠ **I do not understand the `5/8 broken` count, and that is the reason not to ship it.** The check
is `complete && naturalWidth === 0`, which should mean genuinely failed — yet the icons are
visibly present and individually fetchable. A gate whose red I cannot explain trains everyone to
ignore the next real one, which is this module's own stated fear.

**Remaining work, small and specified:** a selector in the PARENT document that bears text, carries
no `<img>`, and moves with the route. The labels are bare text nodes inside the buttons
(`<button class="ht"><img class="ht-i"> Runewords</button>`), so there is nothing to select today —
wrapping them in a `<span class="ht-lbl">` would create one, and that is a `control_ui.html` change,
not a `render_check` one.

⚠ **Cost note for whoever picks this up:** `_serve_console()` is NOT memoised — every
`"serve": True` target boots its own private `control_app`. Seven already do. Add ONE target that
walks all eight tabs, never eight targets.

## 🔴→ ROUTINE I: THREE CAUSES FOUND BY READING THE LOG, NOT BY RE-RUNNING ANYTHING

Routine I had been red for seven days with "no single cause". There were several, and each was
found by reading the CI log — never by running a browser suite on his Mac.

| # | cause | class | where | shipped |
|---|---|---|---|---|
| 1 | `_craftBuffsHtml` read `chronicle`, a variable that was never declared — the name is `grail` | **REAL REGRESSION** | `bible.html:27110` | v2662 |
| 2 | `v2267` renders zero rows on a runner because it deliberately never seeds | **HOST_FIXTURE** | `tests/v2267_…` | `36acf8e2` |
| 3 | `v2193`'s rows carry no `loc`, and the vault door has been gated on it since v2343 | **STALE_ASSERTION** | `tests/v2193_…` | `32275348` |

**Cause 1, confirmed by CI and the zero is measured, not empty:**

```
log size          476,221 bytes   <- an empty log would make any zero meaningless
ReferenceError    10 -> 0
total Error lines 96 -> 71        (-26%)
shard 1/6         failure -> success ; slow 1/2 and slow 2/2 both success
```

⚠ **`js-syntax` is not at fault for missing cause 1, and that matters.** `+chronicle+` is
*syntactically perfect* JavaScript. The gate parses every surface in a real JS engine and passed
this file the whole time — correctly, because **parsing is not executing**. An undeclared
identifier is a runtime fault, and the only lane that executes those paths is Routine I: the lane
that was red. The green was honest; it was answering a different question.

**Cause 3 is the one worth remembering.** Expected 5, received **0** — not 4, not 1. *All* of them,
which was the tell: the gate is per-row and every row was missing the same field.
`_vaultMayClaim(loc)` returns `_VAULT_LANES.indexOf(t) >= 0`, and with no `loc` the lane is `''`,
so `indexOf` returns `-1` for every row. The spec predates that gate by ~150 versions.

⚠ **The code had NOT regressed and I checked before blaming it** — both of v2193's original fixes
are still in place, comments past-tense. ⚠ **And sweeping stopped a wrong fix:** a dozen specs call
`chronicleApply` without `loc` and do *not* fail, because `loc` only matters where a spec asserts
the vault GAINED something. `"the row does not say WHERE it landed"` attributes to
`v1756_inbox_ledger`, which never calls `chronicleApply` — a different fact, left alone.

**Named before the run, not after:** v2193's fixture spells `Andariel’s Visage` with a curly
apostrophe where `bible.html` uses a straight one. Its own `norm()` folds `[’']` and the
`foundOfOurs === 5` guard passes, so it is not the zeroing cause — but if CI returns **4 of 5**
instead of 5, that is the next thread.

## B-90 · A17 RE-PROVED ON ONE QUIET SHA (`32275348`)

Served, 129 text leaves measured — so these counts are readings, not empty-page zeros.
Only the **objectively checkable** defects were re-measured. The rest are design judgements and
are named as such rather than given a manufactured number.

| # | A17 said | measured now | verdict |
|---|---|---|---|
| 1 | "five cards, four of them cut" | **1** at 1440x1000, **2** at 1120x628 | largely fixed; residue named |
| 5 | four dim funnel zeros, "empty and broken look identical" | `filmed`/`banked`/`vault-done`/`releasable` have **no store at all** | **confirmed, now with a mechanism** |
| 7 | "buttons three different widths" | 4 uneven rows; `mini-foc` **83→243px** | **confirmed — and unresolvable as stated, see below** |
| 9 | heading clipped by the scroll container | **0** at both widths | not reproducible |

**#5 gained the thing that was missing.** `one_funnel` says only `triaged` (40/40) and `swept`
(15/40) are dated; the other four rungs record nothing. So those zeros are **never-recorded**, not
measured-and-empty — exactly the distinction he demanded: *"a zero must say WHICH zero it is."*

**#7 exposes a conflict in his own acceptance criteria, and that is the finding.** `.mini-foc`'s
labels run `stash · runes · gems · materials · chronicle · uniques · chronicle · sets` — 4
characters to 19.

- *"Buttons in a row share a width"* → every button as wide as `chronicle · uniques` (243px). Six
  of those is ~1,460px, in a narrow rail.
- *"Nothing ellipsised — if it does not fit, the card is wrong, not the sentence"* → so trimming
  the labels is excluded too.

The only shape satisfying both is a 2-column grid sized to the longest label, costing vertical
space in that rail. ⚠ And shortening the labels is not available: **v1750** records why they are
words and not emoji (*"NO emoji survives in the tab strip or the focus row"*, v1614). **HIS call.**

⚠ `head-tabs` (8 buttons, 89→137px) is **not** counted as a fair hit — those are text buttons with
different labels, where unequal widths are natural.

⚠ **Instrument reach, stated:** the truncation probe requires `textOverflow: ellipsis` **and**
`scrollWidth > clientWidth` — both, because the property alone proves nothing. Text truncated in JS
with a literal `…` would not be counted.

**Not re-proved, not mine:** #2 fleet rows · #3 label/value type scale · #4 raw machine output ·
#6 editorial titles · #8 focal path. *"Nothing is first"* is not a thing a probe can answer.
