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

## A20 · THE RIVER, VISIBLE — ONE STORYLINE INSIDE THEATRE/SHELF · 2026-09-02 · READY

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

## A18 · THE D2R MACRO — HE IS THE CALIBRATION SOURCE · 2026-09-02 · READY

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
> *"self-proving gaps i want taken care of everywhere all round the console i want this logic and
> its own logic coded proving itself! and if it drifts it gets flagged accoridngly and designed
> like we designed to either get fixed or we fix it and the doctor it to be watchdgoged and
> connected to the heart to fix iteself by hardcode design once everything is fixed and locked in
> maybe not just yet the self healing... but in the future no reason for not"*

The flagship. Every gap on the console carries its own proof, flags its own drift, and is wired to
THE HEART (eagle eye · watchdog · corroborator · doctor). ⚠ **Self-healing is explicitly NOT yet** —
he said "maybe not just yet". Build the proving and the flagging; leave the self-repair for later.

## A2 · WILSON EVERYWHERE — and make it actually mean something · 2026-08-30 09:25 + 09:30
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
> *"fix those gaps and anywhere else.. make it unified and logical and coded properly with
> watchdogged and eagle eyed and doctor and corraborotror"*

Said over a table of surfaces against capabilities that was mostly holes — `surfaces registry`
empty across every column, `stash_eye grid` empty across every column, `enlarge (crop + …)` empty,
`OCR worker` present in exactly one. Every surface gets the same four organs, or it is honestly
marked as not having them.

## A4 · THE 3D / 4D PRINTER PIPELINE · 2026-09-01 10:49
> *"we already said if this were to be procesed through our 3D printer it shouldnt matter the
> engines console and filtering and routing system should have done that already and left those
> 104 frames for extra 3D and 4D printer processing and filtering and routing so those other
> worthless frames are check and pruned out alone via templates and techniqued and filters within"*

Said about the prune contradiction — 12 reels prunable, 7 claiming "examined, nothing to take"
while the survey says they held 104 panels. **His point is that the contradiction should never
have reached a human.** The console's own filtering and routing should already have run those
frames through the printer, kept the 104 for extra 3D/4D processing, and pruned the worthless ones
by template, technique and filter — alone.

## A5 · THE SURFACE IS KNOWN AT CAPTURE — KEEP IT, AND PROVE IT BOTH WAYS · 2026-09-01 10:55
> *"the fact was in hand at intake, discarded, and the re-derivation needs footage that no longer
> exists … a logic both ways reverese enginnered and agreeing would also prove to fix this.. so
> connect it to the heart of the console too."*

Measured: 20 reels are named in the evidence and **only 6 still exist — 70% gone**, so the resolver
is re-deriving from film that has been pruned. Two halves: stop throwing the surface away at
intake, AND build the reverse direction so the two must AGREE. Wire it to the heart.

## A6 · THE RETRO ANALYZERS NEED A GATED ACCURACY CHECKER BETWEEN THEM · 2026-08-30 16:01
> *"the retro analyzers need to be accurate and thorough with an extra AI reader if needed
> inbetween them as a gated and accuracy checker"*

An independent reader sitting between the analyzers as a gate, not a second opinion nobody reads.


## A7 · EVERY REEL GOES THROUGH THE SAME PATH — ONE UNIFIED LOGIC · 2026-09-01 19:0x
> *"all reels need to be processed the same way all unified logic"*

No reel gets a special path, a bypass, or a second implementation. One pipeline, one set of rules,
every reel. Any lane that processes a reel differently is either folded in or declared, in code,
as a deliberate exception with a reason.

## A8 · THE TEMPLATES LIVE **INSIDE** THE PRINTER'S FILTERING AND ROUTING · 2026-09-01 19:0x
> *"the templates also need to be within the printer filtering and routing correctly and
> discarding"*

The templates are not a separate pass bolted beside the printer — they are the mechanism the
printer filters, routes and discards WITH. If a template can be removed without the routing
changing, it is not wired in.

## A9 · THE 10-15% LAW — THE ENGINE THROWS THE GARBAGE OUT BY DEFAULT · 2026-09-01 19:0x
> *"withing the 100% reels only 10-15% are worth saving.. the rest should by default within the
> processing engines automaticaly filter the garbage out and leave the information reels with data
> to extract from and then there another layer"*

**A measurable law, and it doubles as the gate.** Of 100% of reels, 10-15% carry data worth
keeping. The engines must reach that ratio BY DEFAULT, automatically, with no human deciding — and
then a further layer works only the survivors. ⚠ If the pipeline is keeping far more than 15%, the
filter is not working; if far less, it is eating data. Either way the number is the alarm.

## A10 · THE FISH DOWN THE STREAM — PROBE ONE REEL THROUGH THE WHOLE RIVER · 2026-09-01 19:0x
> *"remembe the fish needs to go down the stream.. probe it down the stream meaning the reel needs
> to go do the river stream an see that its properly syncned and no gaps... and everything is
> working and collaborating.. and all is working an nothing is stale"*

An END-TO-END probe, not a unit test of each stage. Put one reel in at the top and follow it all
the way down: every stage it touches, in order, asserting at each step that it is synced, that
there is no gap, that the stage actually collaborated with the next one, and that nothing it read
was stale. **This is the only check that can catch two stages that each work and never meet**
([[the-unjoined-end]]). Wire the result to the heart.

## A11 · ARE ALL THE LANES EVEN HERE? — INVENTORY, THEN PROVE EACH ONE · 2026-09-01 19:0x
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
> *"blueprints.. reverse blueprints.. everything"*

Both directions, and they must AGREE. Forward: what the system is supposed to do. Reverse: what the
code actually does, derived from the code. Where they disagree, THAT is the finding — the same
two-way-agreement principle as A5, applied to the whole console rather than to one fact.


## A13 · THE VISUAL HARNESS MUST FEED THE GATE · 2026-09-01 19:1x
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
