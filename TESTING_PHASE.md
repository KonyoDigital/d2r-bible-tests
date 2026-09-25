# TESTING PHASE — hand tests, by scenario

**What:** your 2026-09-25 ruling: *"we still need to do testing pinpointed scenarios and items lists to test and debug manually each ... we are still in the wiring and backend of it all. once we ship everything we will start testing"*.  
**What is in it:** 33 scenarios in 4 areas (Vault · Chronicle · TV·D · Fleet). Each one was checked against the shipped code and your live console on 2026-09-25.  
**How:** pick a scenario, do its steps, and mark its box in the index ✅ / ❌ / ❓.  
**On ❌ or ❓:** paste the scenario ID, the ❌ line that matched, and what the screen showed into a GitHub comment, or tell Claude.  
**Legend:** ✅ pass · ❌ fail · ❓ could not tell · 💳 spends paid reads · ⏸ waits for v-B to merge

## Index

| ☐ | ID | Title | Area | Min | Proves |
|---|---|---|---|---|---|
| ☐ | [VAULT-ATTR-01](#vault-attr-01) | Filmed tooltip → sockets / eth / quality reach the vault row | Vault | 10 💳 | #60 (vp3368, v3369) |
| ☐ | [VAULT-MAGIC-01](#vault-magic-01) | Magic/rare names carry affix vocab; grounding never ticks the Chronicle | Vault | 10 💳 | #53 (v3364) |
| ☐ | [MULE-01](#mule-01) | One Esc closes the mule window on your Mac | Vault | 3 | #174 v-A · REG-1298 |
| ☐ | [VAULT-INTAKE-01](#vault-intake-01) | Inventory read is HELD, stash read is filed to its locker | Vault | 5 | live vault door · v2346 ruling |
| ☐ | [MULE-VB-01](#mule-vb-01) | ⏸ Slot picker offers only this locker's fitting items | Vault | 5 | #174 v-B |
| ☐ | [MULE-VB-02](#mule-vb-02) | ⏸ Stats summed from item text; ranges, never averages | Vault | 5 | #174 v-B |
| ☐ | [MULE-02](#mule-02) | Stepping mules keeps the console alive; numbers match the plate | Vault | 3 | #174 · REG-1071 / REG-1089 |
| ☐ | [VAULT-PROOF-01](#vault-proof-01) | '⚖ n' proof chip per locker; no chip on the public site | Vault | 3 | #105 · REG-1052 |
| ☐ | [MR-01](#mr-01) | A stash read tags magic / rare / grail / base / unknown correctly | Chronicle | 5 💳 | #53 (v3364) |
| ☐ | [MR-02](#mr-02) | A magic item grounds to OWNED, and loses its class | Chronicle | 3 💳 | #53 (grounding) |
| ☐ | [ASK-25](#ask-25) | 'CHOOSE IN INBOX →' lands on the question card | Chronicle | 2-4 | #25 · REG-1297 |
| ☐ | [UNTICK-01](#untick-01) | Does every door respect your standing un-tick? | Chronicle | 5 💳 | nine-un-tick ruling |
| ☐ | [HAND-01](#hand-01) | A hand tick moves every tally by one and banks a 'hand' witness | Chronicle | 1-2 | #166 · v2462 / v2714 |
| ☐ | [REMAIN-01](#remain-01) | The Remaining-page question, and 'I filmed one' | Chronicle | 5 + 2 h 💳 | REG-1230 / #228 · REG-1249 |
| ☐ | [ESC-01](#esc-01) | Esc on the Promote-ALL question answers 'no' (Mac) | Chronicle | 1 | REG-1254 |
| ☐ | [HAVE-01](#have-01) | A read of items you already have changes nothing | Chronicle | 3 💳 | REG-1274 · apostrophe fold |
| ☐ | [NEW-01](#new-01) | A new find ticks itself; every tally moves by one | Chronicle | 2 | shadow-gate ruling · v2714 · REG-1289 |
| ☐ | [REC-01](#rec-01) | ON AIR end to end: one reel, sealed whole, credited | TV·D | 12 💳 | ON AIR door (v2316/v2687) · seal chain |
| ☐ | [REC-02](#rec-02) | Reel …39108 is HELD, never tombstoned | TV·D | 3 + ≤15 wait | REG-1277 |
| ☐ | [REC-03](#rec-03) | OCR + vision workers answer every read, across a respawn | TV·D | +6 (in REC-01) 💳 | REG-1300 |
| ☐ | [REC-04](#rec-04) | Theatre after a relaunch: prompt, closes on view switch, ✕ CLOSE | TV·D | 6 | REG-1284 · REG-1286 / #172 · REG-1255 |
| ☐ | [REC-05](#rec-05) | MINI door: bounded reel, stops itself, credited | TV·D | 4 💳 | MINI door (v2316/v2687, v1605, v2319) |
| ☐ | [REC-06](#rec-06) | Windows eye: held with no D2R, locked with D2R | TV·D | 12 💳 | REG-1250 · REG-1247 · REG-1260 |
| ☐ | [REC-07](#rec-07) | Receipt chips: floor = seen, stash = registered | TV·D | +3 (in REC-01) 💳 | #56 / v2230 · v1506 · v1616 |
| ☐ | [REC-08](#rec-08) | Rolling prune frees only blank duplicates | TV·D | in REC-01 | v2986 prune · LaneCanary |
| ☐ | [RELAUNCH-01](#relaunch-01) | A manual relaunch makes today's fixes live | Fleet | 2 + 12 wait | REG-1286..REG-1303 · relaunch button |
| ☐ | [FLEET-01](#fleet-01) | Each console shows its own counts | Fleet | 5 | #240 · REG-1289 / REG-1296 |
| ☐ | [CLAIM-01](#claim-01) | Restore, never reseed | Fleet | 5 | #239 · REG-1291 |
| ☐ | [FLEET-02](#fleet-02) | The cross-reference names the ALT-only items | Fleet | 5 | #240 (v2213 masks) |
| ☐ | [ALT-01](#alt-01) | ALT parity after a pull | Fleet | 3 (20 elapsed) | #141 · REG-1290 · #225 |
| ☐ | [DOCTOR-02](#doctor-02) | A present machine is not called away | Fleet | 5 over ~1 h | REG-1302 |
| ☐ | [DOCTOR-01](#doctor-01) | A needs-you row next to a Claude-owes row | Fleet | 5 | #223 / #226 · REG-1263 / REG-1282 · #25 |
| ☐ | [ESC-02](#esc-02) | Esc ladder in the chronicle inbox (ALT) | Fleet | 3 | REG-1254 |

## Before you start

- **Relaunch first.** Your Mac console runs code older than the disk: on 2026-09-25 the eagle rows *running code matches disk* and *window runs the document on disk* both read MISSING. Anything you look at before a relaunch tests old code. Order: FLEET-01 steps 1-2 (they need the old window) → RELAUNCH-01 → REC-02's setup, then REC-01 (the first new reel, which REC-02 watches) → everything else.
- **Never press Esc to close a console panel.** Esc on THE STATE OF THIS CONSOLE, the fleet *yours vs theirs* window, the ♥ heart panel or the receipts view closed it AND quit the console on builds before REG-1304 (fixed 2026-09-25; live on your screen once your console relaunches onto it). Until then close panels with ✕ or a backdrop click. Press Esc only where a step says to, and never on an empty console page, because that quits by design. In game, close the stash with its in-game ✕ and never press Esc while the console window has focus.
- **New reels release old ones.** Every ON AIR or Mini recording seals a new reel. The 1st new reel of the phase exposes reel …39108 (REC-02 must watch it). The 2nd permanently releases reel …41906 (REC-05). The 4th exposes reel …57378, REG-1277's untested half. This is worked out from REC-02, REC-05 and the TV·D notes. Reel IDs here are shortened to their last digits, so search Finder for those digits.
- **👁 EYES** is on PRIMARY (Grok reads first). REC-01, REC-03 and REC-05 are written for OFF (Claude reads). Switch it back to PRIMARY after End Session.
- **💳 Paid reads:** before any vault or chronicle sweep, press *price the sweep* (free) and read the quote. On 2026-09-25 a full-reel sweep read 236 pages in 40 min and banked nothing.
- **Doctor rows:** read them through `/api/status` (its eagle summary). On 2026-09-25, `/api/eagle` did not answer within 30 s.
- **Figures** such as 309/403, 134/135, 43 unsure or 14 owned are 2026-09-25 readings, and they move as you play. Compare relations, not the literal numbers.

---

## 1 · Vault, mules and item facts

Includes #174 (mule window) and #60 (item facts). Baseline on 2026-09-25, from a read-only GET /api/vault_ledger: 14 grounded rows and 44 seen-once rows, both stores about 5.8 days old, and no witness carries prompt vp3368 or any socket/eth/quality value. The stored 2026-09-19 sweep already tags its 43 unsure rows: GRAIL 14 · BASE 12 · MAGIC 8 · RARE 4 · UNKNOWN 5.

<a id="vault-attr-01"></a>
### VAULT-ATTR-01 — #60: a filmed tooltip of an ethereal socketed base reaches the vault row with sockets, eth and quality

**Proves:** #60 end to end on your own footage: a filmed tooltip's sockets, ethereal and quality reach the vault row (prompt vp3368 → witness carry v3369 → vault_seen → doctor row). Also proves one base name can hold two items with different facts. Today it is proven only by fixtures.  
**Setup:** Console open on your Mac, ON AIR available. In one stash tab you need: (1) an ETHEREAL socketed base; (2) a NON-ethereal copy of the SAME base name, with a different socket count or 0 sockets; (3) one unique with no sockets. No copy should be Superior, because 'Superior' is part of the name and would make a different row. All three names must be absent from your vault ledger (open 📒 ledger first). The reason: a second look at a name already seen once GROUNDS it. The new sighting, the one carrying the vp3368 facts, then goes to the grounded ledger and never into vault_seen.json, and vault_seen.json is the only store the doctor row reads. The older seen-once row stays in vault_seen.json either way. Before starting, open the TV·D view → ⚙ ADVANCED → ⚙ RARE PATHS → 🦅 eagle and write down the row 'item facts captured'. Expected today: '?' mark, 'no sighting has been read by prompt vp3368 yet … UNMEASURED'.

**Items:**
- An ethereal socketed polearm base, e.g. an eth 4-socket Giant Thresher, Colossus Voulge or Cryptic Axe (merc Insight/Infinity bases). Why: eth=true and sockets=4 are both non-default values, so a reader returning null or 0 fails loudly.
- A non-ethereal copy of the SAME base name (another socket count, or 0). Why: it proves one name holds two items with different facts, and a 0-socket copy proves 0 is banked as 0 and not null. If you have no eth/non-eth pair, use two non-eth copies of one base with different socket counts (e.g. a 4os and an unsocketed Monarch). That still proves one-to-many and 0-vs-null, but eth=true is then NOT_EXERCISED.
- One unique NOT already in your ledger (e.g. Nagelring, which is absent from the 2026-09-25 read). Why: it proves quality='unique' is read from the gold text, and that sockets are never invented for an unsocketed item. Avoid War Traveler, Sacred Rondache, Goldwrap and Magefist: they are already in your vault ledger, so re-filming them adds a second look instead of a fresh first one.

**Steps:**
1. Start a recording (ON AIR). Open the stash with the inventory beside it, on the tab that holds the three items.
2. Hover each item for 2–3 s so its WHOLE tooltip is on screen and not clipped at the panel edge. Order: the ethereal base first (its last line should read 'Ethereal (Cannot be Repaired), Socketed (N)'), then the non-ethereal copy, then the unique.
3. Do all three hovers in one stash opening, with no pause of 3 minutes or more between them. A gap of 180 s or more between two still screens (REOPEN_GAP_MS) opens a second 'look', and that could ground the names.
4. Optional live cross-check while still ON AIR: in the theatre beat, the '📖 IT SAW' row should list each socketed name with a 🏦 badge and a ⏣N pill. The unique gets no pill. This is the live lane, a different reader from the vault sweep.
5. Stop the recording and let the reel seal.
6. Console, TV·D view, VAULT ACCUMULATOR card (hidden on the Sessions homepage): press 'price the sweep' and READ the quote. The first price after new footage can take minutes; if it says 'gave up after 3 minutes', tap again. If the quote covers more than this one new reel, or tens of pages, stop and ask.
7. Press 'run it for real' and wait until the panel settles. Your new names should sit in the '👁 UNSURE · seen once' column.
8. Press 🦅 eagle again and read 'item facts captured'.
9. Press 📒 ledger. The two new names should appear under 'SEEN ONCE — held until a second sighting'.
10. In a browser tab, open the console's own address (port 17772) at /api/vault_ledger (a read-only GET). Under "seen", find the base's name and read its witnesses[] entries.

**✅ Expect:** The 🦅 row 'item facts captured' changes from '?' to '✓' and reads 'k of n sighting(s) read by vp3368 carry at least one of sockets/eth/quality'. k and n count NAMES (rows), despite the word 'sighting(s)'. Expect n ≥ 2 (the base name and the unique) and k ≥ 1. 📒 ledger: the base name appears once under SEEN ONCE, reading 'stash · … · N witnesses' plus '👁 AI saw it Nm ago'. N counts sighting ENTRIES (one per frame whose tooltip was read), not looks, so N ≥ 2 and may be higher. In the raw witnesses for the base, at least one entry has sockets = the tooltip's N, eth: true and promptVer 'vp3368'. At least one other entry has eth false or null (never true) and its own socket count: 0 if the copy visibly has none, or null. Quality on a socketed normal base is 'white' or null, because the item name prints GREY and the prompt's colours are white/blue/gold/unique/set; record which. The unique's entries show quality 'unique', eth false or null, and sockets 0 or null (never > 0). No on-screen panel prints the socket or eth values themselves (see the lists at the end).

**❌ Fail looks like:**

- (a) The doctor row turns ⚠ MISSING 'N sighting(s) read by vp3368 and NOT ONE carries sockets, eth or quality': the template keys stopped coming back.
- (b) It stays '?' after a sweep that listed the names: the witnesses carry no promptVer, or the names grounded (their new witness went to the grounded ledger, not vault_seen).
- (c) The ethereal base has no entry with eth true while 'Ethereal' was on screen, or no entry with sockets N while 'Socketed (N)' was visible.
- (d) The two copies produce entries with identical facts, or only one copy's entries exist.
- (e) The doctor row is ✓ only because of the unique's quality while every base entry is null: that is a partial pass, record it as such.

**🔎 Debug first:** First, the VAULT ACCUMULATOR's own verdict sentence (vault_retro._verdict tells apart no footage, no stash panels, panels with no readable names, and so on). Then vault_last_result.json (was the reel read; do the names appear with vocab and witnesses) and vault_seen.json (witness keys sockets/eth/quality/promptVer). For the reader side: VAULT_READ_PROMPT (VAULT_PROMPT_VER vp3368) in tv/tv_diablo.py. If the names never appear at all: vault_doctor.py ('why is the vault empty').

**Cost:** About 10 min of your time. It spends ONE paid vault sweep (a standing approval for vault reads, #60). Read the 'price the sweep' quote first: a 2026-09-25 full-reel sweep reportedly read 236 pages in 40 min and banked nothing.  
**Unknowns:** UNKNOWN whether the sweep's panel gate recognises your new reel as a stash reel. If it does not, the verdict sentence says so, and that is the finding. UNKNOWN which other owed reels the quote will include. UNKNOWN how many witness entries one 2–3 s hover produces (one per tooltip frame read). Quality for a grey (socketed normal) name: 'white' and null are both honest. For a non-ethereal item the prompt allows eth false or null. Nothing on screen renders the per-item facts, so the per-item check needs the raw GET JSON.  
**Read from:** tv/tv_diablo.py:VAULT_READ_PROMPT · tv/vault_retro.py:normalize_item, _sockets_of, _quality_of, REOPEN_GAP_MS · tv/control_app.py:vault_seen_save · tv/console_doctor.py:_check_the_item_facts_are_reaching_the_row · tv/control_ui.html:_vaultNames, thSocketPill

<a id="vault-magic-01"></a>
### VAULT-MAGIC-01 — #53: magic and rare names read by the vault lane carry the game's own affix vocabulary, and grounding them never ticks the Uniques Chronicle

**Proves:** #53 on real vault rows: the game's own affix vocabulary tags magic and rare names, and grounding them never ticks the Uniques Chronicle. The tags can already be read for free. A fresh tag, and where a grounded magic/rare row lands, have never been shown.  
**Setup:** The same console and recording path as VAULT-ATTR-01. Before filming, write down: the 🦅 eagle row 'item vocabulary'; your current Uniques tally; and the Vault population line ('X owned · … · Z filed to mules · W still loose'). You must still hold Shadow Amulet of the Whale, Death Loop and Storm Scarab (all seen once, stash lane, about 6+ days ago).

**Items:**
- Shadow Amulet of the Whale: YOURS, seen once (stash). Parses MAGIC 'shadow + amulet + of the whale'. Refilming it gives the second look, so it grounds and exercises the register-to-board half.
- Death Loop: YOUR rare ring, seen once. Parses RARE 'death + loop' (rare prefix + ring suffix).
- Storm Scarab: YOUR rare amulet, seen once. Its UNKNOWN tag is the control that nothing guesses. Read it in step 1, because once it grounds, its row no longer carries a tag.
- One magic or rare item whose exact name is NOT in the 📒 ledger, e.g. any magic grand charm or rare ring/amulet you have not filmed. Do not use Sullied Grand Charm of Blight: it is already GROUNDED in your ledger. Why: a fresh name stays seen-once, so its vocab tag is visible in result.unsure.
- Control, free in step 1: Sacred Rondache (YOUR white paladin shield base, seen once) must read BASE. Do not refilm it for this test, because grounding it removes its tag.

**Steps:**
1. FREE, BEFORE ANY SPEND: open the console's address (port 17772) at /api/vault_sweep (read-only GET). In result.unsure, read vocab and vocabWhy for Shadow Amulet of the Whale, Death Loop, Storm Scarab and Sacred Rondache. Then 🦅 eagle → 'item vocabulary'.
2. ON AIR: open the stash and hover Shadow Amulet of the Whale, Death Loop and Storm Scarab for 2–3 s each, full tooltip visible. Also hover ONE magic or rare item whose exact name is NOT in the 📒 ledger (check first).
3. Stop and seal. In the VAULT ACCUMULATOR press 'price the sweep' (read the quote), then 'run it for real'.
4. Read the columns '🏦 OWNED · corroborated (N)' and '👁 UNSURE · seen once (N)', and the apply button's label.
5. 🦅 eagle → read 'item vocabulary' again.
6. GET /api/vault_sweep again. In result.unsure find the new item's row and read vocab and vocabWhy.
7. OPTIONAL, AND IT WRITES TO YOUR BOARD: press 'register N ✓'. N is EVERY row in OWNED, meaning the 14 already-grounded rows (potions, the Horadric Cube, charms, Magefist, Bone Break…) plus the newly grounded ones, not just the three. Skip it if you do not want those filed. If pressed, read the note '✓ k row(s) into your vault · …'.
8. If registered: Board → Vault → type each name into 'Find an item across your mules — which alt is it on?'. Re-read the Uniques tally and the population line. Relaunch the console and look again.

**✅ Expect:** Step 1 (as of the 2026-09-19 result): Shadow Amulet of the Whale MAGIC 'shadow + amulet + of the whale'; Death Loop RARE 'death + loop'; Storm Scarab UNKNOWN 'no parse against the lexicon' ('scarab' has no display string in the game's tables); Sacred Rondache BASE 'exact base type'. 'item vocabulary' ✓ ending '… it can name 38 of 43 unsure name(s)', provided the lexicon still matches your install. After the sweep: OWNED lists the 14 already-grounded rows plus Shadow Amulet of the Whale, Death Loop and Storm Scarab, if their second look clears the 0.55 confidence floor. The button reads 'register N ✓' with N ≥ 17. The never-filmed item sits in UNSURE, and its row carries vocab MAGIC or RARE with a parse in vocabWhy. Grounded rows carry no vocab tag. 'item vocabulary' stays ✓ and its N of M changes by the names that left and entered unsure; record both numbers. If registered, predicted by reading suggestMule and NOT run: Shadow Amulet of the Whale files to UNI-SMALL ('jewelry/charm — base: …'). Death Loop and Storm Scarab are parked in UNI-WEAPONS with the reason 'weapon — base: Death Loop' / '… Storm Scarab'. No path files any of them to MAGIC & RARE. None of the three appears as a find in the Uniques Chronicle, and all three are still filed after the relaunch. The Uniques tally must not move because of these three. If it moves, a grail name among the 14 re-sent rows that was not yet ticked did it, and the Chronicle ledger row names which.

**❌ Fail looks like:**

- (a) A magic or rare name tagged GRAIL or BASE, or Storm Scarab tagged MAGIC or RARE (a guessed parse).
- (b) 'item vocabulary' collapses to 'it can name 0 of M' while M > 0: the lexicon has stopped being consulted.
- (c) Shadow Amulet of the Whale, Death Loop or Storm Scarab appears as a find in the Uniques Chronicle.
- (d) One of them is filed, then gone after the relaunch.
- (e) Routing: record where each landed. The predicted UNI-WEAPONS park for the rare ring and amulet is a routing question for your ruling, not a pass.

**🔎 Debug first:** The doctor row 'item vocabulary' (MISSING there means the lexicon is stale against the install; that needs a regenerate, not a read fix). For the classification: result.unsure[].vocab in vault_last_result.json. For the board landing: the vault ledger rows the apply writes (source 'vault-sweep' / 'auto-assign', via kaiChronicleRecord), d2r_owned vs d2r_foundLog, and d2r_muleAssign in YOUR board store (the pywebview WebKit store, not Chrome's).

**Cost:** About 10 min of your time plus one paid vault sweep (standing approval). Price it first. Step 1 is free.  
**Unknowns:** Where a grounded magic/rare row lands was established by READING suggestMule, not by running it. The one-hop inbox fold (d2rInboxEngine) could re-route a name, so record what the screen shows. UNKNOWN whether you have pressed 'register' before. If you have not, the 14 re-sent rows (potions, Horadric Cube, charms) will also be filed by the same park rules. The exact N of M after the sweep depends on what the new sweep rewrites into vault_last_result.json.  
**Read from:** tv/affix_lexicon.py:classify · tv/vault_retro.py:_vocab_of, apply_payload · tv/console_doctor.py:_check_the_item_vocabulary_can_name_his_loot · bible.html:vaultAccumApply, _mayVault, toggleOwned, _tvExtraRemember, suggestMule

> **Note:** Overlaps MR-02: both ground Shadow Amulet of the Whale and Death Loop. Run only one of them. Once either has run, those names no longer carry a tag, so do step 1 (free) first.

<a id="mule-01"></a>
### MULE-01 — #174 v-A: on YOUR Mac console, one Esc closes the mule window back to the Vault, from both focus positions

**Proves:** #174 v-A / REG-1298 on your Mac's real WKWebView with a physical key: one Esc closes the mule window from every focus position. Proven so far in headless Chrome and on GrokBot's Linux WebKit seat (its REFUTE turned out to be an instrument fault). Never tested on your Mac.  
**Setup:** Console on your Mac in its native window, on a build that carries #174 (the console relaunches itself onto new builds). If clicking a locker shows the old single ID card instead of three columns, the board is stale. SAFETY: never press Esc unless a window or overlay is visibly open, and never press it twice in a row. With the Vault tab showing and nothing open, an Esc from the console chrome sends the console to its TV·D home. A further Esc there, with nothing open, QUITS the console by design (/api/quit 'escape-empty-stack').

**Items:**
- UNI-WEAPONS locker (any locker works). Why: it is the exact locker in GrokBot's REFUTE, so a pass on your Mac closes that thread on the same surface.

**Steps:**
1. CONTROL (safe, same surface): header tab 'Vault' → 'The Vault — Mule Manager' shows the locker plates. Click into the box 'Find an item across your mules — which alt is it on?', type x, press Esc ONCE. The box must empty. This proves your keyboard's Esc reaches the board, and an Esc typed in a text box can never quit anything.
2. Click the UNI-WEAPONS plate once. Click nothing else, and press Esc ONCE.
3. Click UNI-WEAPONS again, click an empty part of the mule window's own header strip (not a button), and press Esc ONCE.
4. Click UNI-WEAPONS again, click the CONSOLE's own chrome outside the board (an empty part of the console header bar, not a tab, not a button), and press Esc ONCE.
5. Click UNI-WEAPONS again → centre tab 'Calculations' → read the rows → close with the '✕ close (Esc)' button (no key).

**✅ Expect:** The window covers the Vault fullscreen with three columns. LEFT: Equipment (10 empty doll slots, weapon-set buttons I/II, a 10×4 inventory grid), then Primary skills / Mercenary / Loot filter / Strengths and weaknesses, each saying 'Nothing fills this yet. …'. CENTRE: tabs Stash / Skill tree / Calculations, then Notes. RIGHT: Locker (Kind 'storage locker', Character 'none bound'), Summary, and Stats with Normal/Nightmare/Hell, every row reading UNKNOWN. The header shows the locker name, an 'Items N' box, a DISABLED '⇪ Import .d2s', the chip 'Esc closes · ← → steps mules', and '✕ close (Esc)'. After EACH single Esc in steps 2–4 you are back on the Vault tab with the locker plates, the window is gone, and the console is still up. Calculations shows 'Mules they fill (140 cells each)' and 'Trade value (high · med)' as two numbers like '2 · 5' (no 'very high' column). Nothing is clipped, and nothing scrolls sideways at your window width.

**❌ Fail looks like:**

- (a) Esc leaves the window on screen: the board's own Esc did not fire.
- (b) Only in step 4: the console jumps to its TV·D home (the mule window gone, or stuck underneath). The console probe did not see the dialog, so it ran shellHome. Do NOT press Esc again from there.
- (c) The console window disappears.
- (d) The CONTROL fails, meaning the text box did not empty: the key never reaches the board, which is an instrument or focus fault, not the window.

**🔎 Debug first:** If the control fails, suspect key delivery or focus first (GrokBot's lesson). If steps 2–3 fail: the board keydown at bible.html:39708. If only step 4 fails: the console Esc probe in tv/control_ui.html (~21416-21457). Its selector '[role="dialog"]:not([hidden])' must match #vault-detail, and _fVis must get a client rect in WKWebView. If the console quit: the console log line '📺 window gone (api-quit:…)' names the caller.

**Cost:** 3 minutes, no paid reads, no game needed.  
**Unknowns:** Which element holds keyboard focus in macOS WKWebView after a click inside the board iframe has not been measured. Linux WebKitGTK is a different engine build, so GrokBot's pass is not evidence for your Mac.  
**Read from:** bible.html:openMuleCard, vaultCloseCard, board Esc keydown · tv/control_ui.html:console Esc probe, empty-console quit · tv/test_the_mule_window_is_the_planner_shell.py

> **Note:** This is also the backlog item #174 "Esc REFUTES on WebKit": the first real test on your Mac.

<a id="vault-intake-01"></a>
### VAULT-INTAKE-01 — Live ON AIR: an item read in the INVENTORY is HELD, not vaulted; the same item carried into the STASH is filed to its locker

**Proves:** The live door that actually files a hovered stash item (the agent's LootLifecycle): an inventory read is HELD, and a stash read with a chain is VAULTED to its locker. Also tests your v2346 ruling against the 30 s HOLD commit. Proven only by code reading and fixtures.  
**Setup:** Console ON AIR during a normal run. Use a unique you have ALREADY ticked in the Chronicle but have NOT filed in any locker, so the Uniques tally cannot move. Pick it up FROM THE FLOOR in this session: the stash commit needs a floor or inventory chain from this session, otherwise the item is refused 'stash-no-chain'. On the board Vault card, write down the population line and the target locker's plate count.

**Items:**
- Nagelring or Dwarf Star (ITEM_VALUE 'low', rings). Why: common drops, 1×1, and 'low' avoids both the SHARED and the throw-out exits, so slot routing to UNI-SMALL is exercised.
- Blood Crescent (ITEM_VALUE 'trash'). Why: it must land in 🗑 throw-out review, still owned, with the TRASH reason. That separates 'advice' from 'deletion'.
- War Traveler (ITEM_VALUE 'high'). Why: it must file to SHARED STASH, and it then appears in the SHARED STASH window, which lists items assigned there. Use it only if your copy is not already filed.

**Steps:**
1. Pick up the unique. Open the INVENTORY ONLY (stash closed), hover it for 2–3 s with the tooltip fully visible, then close the inventory within about 20 s.
2. In the console's live read feed, the read line for that frame should read '⏳ holding inventory … · HOLDING NAME (≥30s or stash)'. In the theatre beat, '📖 IT SAW' shows the name with 🎒.
3. Board → Vault: the population line and the '#vault-status' text beside the card title must be UNCHANGED.
4. Open the stash with both windows up, move the item INTO the stash, and hover it there (in the stash grid, not while it is still in the inventory) for 2–3 s.
5. Live read line: '🏦 vaulted stash … · VAULT NAME'. Theatre beat: the name carries 🏦.
6. Board → Vault: read the status text and the population line, then type the name into 'Find an item across your mules — which alt is it on?'.
7. OPTIONAL, YOUR RULING: with a SECOND unique (e.g. Dwarf Star), hover it in the inventory only, wait 40 s with the inventory still open, and hover it again. Then check the Vault.

**✅ Expect:** After the inventory-only hover (step 3): no vault change (same 'owned' count, no '📺 TV vaulted' text). After the stash hover: the status reads '📺 TV vaulted: NAME → LOCKER', or '📺 TV vaulted (throw-out advice): NAME — trade value TRASH — …' for a trash-tier item. The population line's 'owned' goes up by 1, and the finder shows the name '→ <locker>'. Destination by the planner's rules (traced in suggestMule): a 'high' item → SHARED STASH ('high trade value — keep close in the shared stash'); a 'trash' item → 🗑 throw-out review (still owned); a 'low' ring such as Nagelring or Dwarf Star → UNI-SMALL (its base Ring matches the jewelry rule). The '#vault-status' text is transient, so the finder and the plate count are the durable checks. Optional step 7: code reading predicts the second hover, 30 s or more after the first, commits the item ('vault:hold') and files it without any stash. That contradicts your v2346 ruling; record what happens.

**❌ Fail looks like:**

- (a) The vault gains the item within 30 s of an inventory-only hover: a leak.
- (b) The read line says '🏦 vaulted' but the board never changes: the TV feed or tvVaultRegister refused. Look for a 'route-failed' row, or a feed that is off.
- (c) The stash hover is tagged 'stash-no-chain' and nothing is filed: the floor/inventory chain was lost (e.g. a console restart in between).
- (d) A trash-tier unique is filed onto a UNI-* locker.
- (e) A high-value item is filed to UNI-* instead of SHARED STASH, with no manual placement of yours to explain it.

**🔎 Debug first:** The live read line's lifecycle note first (HOLDING / VAULT / stash-no-chain / hold-low-conf). 'hold-low-conf' means no Horadric Cube or tome was visible in the inventory AND the read confidence was below 0.75, so nothing was held. Then the theatre beat's WHERE badge: no badge means the reader returned no names_loc. Then the board's chronicle ledger row for the name, then suggestMule's answer for it.

**Cost:** About 5 min inside a normal run. ON AIR live reads only, no vault sweep. It files real items into your vault (additive), which is the product doing its job.  
**Unknowns:** UNKNOWN whether the live reader reports names_loc for a hovered stash item on your current prompt. Without it, the stash-side split falls back to the panel scene. UNKNOWN whether the console's board TV feed is switched on in your session. Whether the 30 s inventory HOLD commit should exist at all under your v2346 ruling is your call.  
**Read from:** tv/tv_diablo.py:LootLifecycle.process, _track_pending, _on_stash · bible.html:tvVaultRegister, kaiChroniclePropose, _vaultMayClaim, suggestMule, ITEM_VALUE

> **Note:** Step 7 is your ruling to make: record what happens, then decide whether the 30 s inventory commit should exist.

<a id="mule-vb-01"></a>
### MULE-VB-01 — PENDING-v-B: clicking a doll slot offers only THIS locker's items that fit it; equip, hover, unequip, persist, Esc order

> ⏸ **PENDING v-B.** This is not on your screen until v-B merges to main and the console relaunches onto it. Skip it for now.

**Proves:** #174 v-B: the equip store, a slot picker that offers only this locker's items that fit, one tooltip style, and Esc closing the picker before the window. It exists only in the unmerged v-B worktree.  
**Setup:** Only after v-B merges to main and the console has relaunched onto it. The UNI-ARMOR locker must hold at least gloves and a belt.

**Items:**
- Magefist: YOURS (grounded in your vault ledger; ITEM_VALUE 'low'; base Light Gauntlets, so suggestMule files it to UNI-ARMOR). The positive case for the gloves slot.
- Goldwrap: YOURS (seen once in your stash; 'low'; Heavy Belt, which the armor word rule files to UNI-ARMOR). The negative case: it must be LEFT OUT of the gloves picker and offered in the belt picker.
- War Traveler (ITEM_VALUE 'high' → SHARED STASH): if it sits there, it proves the picker is locker-scoped, because SHARED has no doll.

**Steps:**
1. Vault → click the UNI-ARMOR plate → click the gloves slot (🧤) on the doll.
2. Read the picker header ('gloves · k of N fit') and its footer ('Left out: … of N — …').
3. Choose Magefist.
4. Hover the gloves slot.
5. Look at the Stash tab grid and the 'Items N' box.
6. Right-click the gloves slot (or focus it and press Delete), then re-equip Magefist.
7. Relaunch the console, reopen UNI-ARMOR.
8. Click the belt slot so the picker is open → press Esc ONCE → press Esc ONCE more.
9. Open the SHARED STASH plate.

**✅ Expect:** The picker lists ONLY gloves from UNI-ARMOR. Magefist's line reads '<base> · gloves — from the game's unique / set table', where the base is Light Gauntlets as the table spells it. The footer names every item left out and why, e.g. '1 fits another slot: Goldwrap (belt)', plus any name under 'have no slot on record, so they are not offered'. After choosing, the picker closes, Magefist's art sits in the gloves slot, and focus returns to that slot. Hover shows the same item tooltip card the rest of the board shows for Magefist. 'Items N' is unchanged, but Magefist's tile is gone from the stash grid (a worn copy is counted and packed nowhere). Right-click, the slot's ✕, or Delete unequips. After the relaunch Magefist is still worn (d2r_muleEquip persists). The first Esc closes only the picker; the second closes the window to the Vault. SHARED STASH opens its 5-page shared view with no doll, by design.

**❌ Fail looks like:** Goldwrap (a belt) offered for the gloves slot; an item from another locker offered; Magefist still drawn in the stash grid while worn; a different tooltip style; the equip lost after the relaunch; the first Esc closes the whole window; a doll appearing on SHARED STASH.

**🔎 Debug first:** _mpFit's answer for the name (which source resolved its base), then MULE_BASE_SLOT (generated by tv/mule_slot_map.py in the worktree from your install), then the d2r_muleEquip store in your board.

**Cost:** About 5 min, no paid reads.  
**Unknowns:** Which items your board actually files in UNI-ARMOR (your board store was not read). If Magefist lives elsewhere, use any gloves/belt pair from one locker. v-B is not merged, so labels may still change.  
**Read from:** bible.html (v-B worktree):_mpFit, _mpEqPlace, _mpWornFor, _mpPick, _mpChoose, _mpSlotKey · bible.html:openMuleCard · tv/test_the_mule_window_equips_and_says_its_source.py

<a id="mule-vb-02"></a>
### MULE-VB-02 — PENDING-v-B: the Stats column sums worn gear from item text, shows a RANGE for a rolled stat, and never an average or a made-up number

> ⏸ **PENDING v-B.** This is not on your screen until v-B merges to main and the console relaunches onto it. Skip it for now.

**Proves:** #174 v-B stats: worn gear is summed from item text, a rolled stat shows a RANGE, EXACT comes only from a .d2s, and anything else is UNKNOWN with a reason. Proven only by pure-function cases.  
**Setup:** After v-B merges. Magefist in the UNI-ARMOR gloves slot and Goldwrap in its belt slot (from MULE-VB-01). Optionally, a helm with a rolled MF range from the same locker (Tarnhelm or Stealskull).

**Items:**
- Magefist (YOURS): a fixed +20% FCR, so FCR must show exactly '20%' TEXT.
- Goldwrap (YOURS): a fixed 30% MF plus 10% IAS. It proves summing across two items and a second stat row.
- Tarnhelm or Stealskull (whichever you have filed in UNI-ARMOR): a ROLLED MF line. It is the one item that makes 'range, never averaged' visible. Stealskull also moves IAS and FHR.

**Steps:**
1. Open UNI-ARMOR with Magefist and Goldwrap worn → right column STATS.
2. Read these rows and their values: Faster Cast Rate, Magic Find, Increased Attack Speed, Faster Hit Recovery, Fire Resistance, Life, Strength, Defense.
3. Hover the Magic Find value to read its source breakdown.
4. Equip a helm with a rolled MF line (Tarnhelm '25-50%' or Stealskull '30-50%') and re-read Magic Find (plus IAS and FHR if it is Stealskull).
5. Type 'magic' in the Stats Search box, then resize the window. The caret must stay in the box.

**✅ Expect:** Faster Cast Rate '20%' TEXT (Magefist '+20% Faster Cast Rate'). Magic Find '30%' TEXT (Goldwrap). Increased Attack Speed '10%' TEXT (Goldwrap). Faster Hit Recovery and Fire Resistance '0%' TEXT: the worn text adds none, and these rows read 'what the worn gear adds'. Life '0' TEXT for the same reason. Strength UNKNOWN ('… +stats on gear are not read yet'). Defense UNKNOWN ("defense needs the character and each armor piece's own rolled defense"). The hover reads like 'what the worn gear adds · Magefist — by name, ITEM_CODEX text: none · Goldwrap — by name, ITEM_CODEX text: 30%'. With Tarnhelm worn, Magic Find becomes the RANGE '55–80%' TEXT. With Stealskull it is '60–80%', IAS becomes '20%' and FHR '10%'. It is never a single middle number like 67%. No cell says EXACT, because EXACT needs a .d2s import (v-C). The legend reads 'What the worn gear adds, weapon set I · EXACT the rolled value from a .d2s · TEXT the item's own text, placed by name — a range when it rolls, never averaged · MIXED both, or a part still UNKNOWN (≥)'.

**❌ Fail looks like:** An averaged single value (e.g. 67%). Any EXACT tag with no import. A number on Strength, Defense or another row the gear cannot answer. MF not summed across items. A '≥' or MIXED tag with only by-name items and no unknown part. The Search caret lost on resize.

**🔎 Debug first:** _mpContrib for each worn name (which text source was read), then _mpParseProp on the exact property line (ITEM_CODEX props), then _mpSumStat.

**Cost:** About 5 min, no paid reads.  
**Unknowns:** Whether you own Tarnhelm or Stealskull in the same locker. Without a rolled MF item in one locker, the range half is NOT_EXERCISED. Row wording may change before v-B merges.  
**Read from:** bible.html (v-B worktree):_mpParseProp, _mpContrib, _mpSumStat, MULE_STATS · bible.html:ITEM_CODEX

<a id="mule-02"></a>
### MULE-02 — #174 + REG-1071: stepping a multi-mule locker with ← → and the ◄ ► arrows keeps the console alive, and the window's numbers match the locker plate

**Proves:** The mule packer seen through the v-A window, plus REG-1071 / REG-1089 on your machine: stepping between mules never quits the console, and the window's numbers match the locker plate.  
**Setup:** A locker whose plate shows the '×N🧍' badge (N ≥ 2). If no locker spans two mules on your board, mark NOT_EXERCISED (your GrokBot mirror reportedly shows 19 owned items, which fit on one mule).

**Items:**
- The locker with the most items on your board. Why: only a locker over 140 cells has a Mule 2/3 to step to. The v2212 case (16 Colossus Blades: mule 1 holds 120 cells, mule 2 holds 8) shows big weapons spill first, so UNI-WEAPONS or SOCKETED are the likely candidates.

**Steps:**
1. On the Vault shelf, hover the plate's count. It reads 'T items · C cells, packed across N mules (each = a 10x10 stash + a 10x4 inventory). Open the locker to see the packing.' Write down T, C and N.
2. Click the plate. Check the 'Items' box and the 'Mules in this locker' tabs (Mule 1 … Mule N).
3. Centre tab 'Calculations': read 'Items in this locker', 'Mules they fill (140 cells each)', 'Items on Mule 1', 'Cells placed / capacity'.
4. Click an empty part of the mule window (not the Search box) so the keys go to the board. Arrow keys are NOT forwarded from the console chrome. Press → N times, then ← once.
5. Click the ► arrow in the 'Mules in this locker' header through every mule (2→3 is the step that once killed the console), then click the Mule tabs directly.
6. Press Esc once. Do not press it again after the window closes.

**✅ Expect:** 'Mules they fill' = N, and Summary shows 'Mules N'. 'Items' = T, unless a name is owned in several copies: the plate counts NAMES, while the window counts physical copies (e.g. 3 Threshers = 3). 'Cells placed / capacity' reads C / (140 × N), unless the Notes say items exceed the mule cap. Each → steps 'Mule k / N' and the stash grid re-packs to a different set of tiles. After Mule N it wraps to Mule 1. The 'Items on Mule k' values add up to 'Items' (minus any overflow the Notes name). The console window stays up throughout, and Esc returns to the Vault.

**❌ Fail looks like:** The console window closes on an arrow click (the REG-1071 trap). The plate's N or C disagrees with the window's figures, with no copies or overflow to explain it. An arrow key steps mules while the Search box has focus. A mule page is empty while its count says items sit on it.

**🔎 Debug first:** The console log line '📺 window gone (api-quit:…)'. 'api-quit:UNATTRIBUTED' IS the finding (only the Esc empty-stack handler may quit, and it names itself). For the numbers: bible.html _muleLoad, the one packer that both the plate and the window ask.

**Cost:** About 3 min, no paid reads.  
**Unknowns:** Whether any of your lockers spans 2+ mules today (your board store was not read).  
**Read from:** bible.html:_muleLoad, MULE_CAP, _muleSetPage · tv/control_app.py:_mark_window_gone, /api/quit

<a id="vault-proof-01"></a>
### VAULT-PROOF-01 — #105 proof chip: '⚖ n' on each locker equals how many of the 14 ledger-proven names it holds, and the chip is ABSENT on the public site

**Proves:** REG-1052 / #105: each locker's '⚖ n' chip counts the ledger-proven names it holds, and a failed ask shows NO chip (never a '⚖ 0'). Never checked on your screen against your real 14 proven names.  
**Setup:** The console running, with the board inside it. Also your PHONE (a different device) with the public site's Vault tab. A browser on the same Mac could still reach the console and would show the chip.

**Items:**
- Magefist: grounded (2 witnesses) and a real keeper that files by slot to UNI-ARMOR. It is the one proven name that is not a consumable, so a non-zero chip on its locker is meaningful.
- Heart of the Oak: grounded and a runeword, so it should file to RUNEWORDS. It checks exact-name matching on a runeword.
- Bone Break / Renewed Black Cleft: grounded, but never assigned to any locker. They show that the chip can only count what is filed.
- Horadric Cube, Radiance (103 witness entries), the two potions: grounded but not locker keepers. Why they matter: the chip MARKS and never filters, because most of the 14 proven names are consumables (#105's own finding).

**Steps:**
1. TV·D view → ⚙ ADVANCED → ⚙ RARE PATHS → 🦅 eagle → read the row 'the vault can say what it proves'.
2. Vault tab: on each locker plate read the '⚖ n' chip, and hover one to read its title.
3. Open UNI-ARMOR and RUNEWORDS (or use the finder box) and check whether Magefist and Heart of the Oak are filed there.
4. On your phone, open the public site → Vault.

**✅ Expect:** The eagle row reads ✓ '14 of 14 ledger row(s) clear the 2-witness bar, so the chip has something to say' (the 2026-09-25 read: 14 grounded rows, each with 2+ witness entries), as long as no sweep has run since. Every plate on the console board, SHARED STASH included, carries '⚖ n'. Its title reads 'n of T item(s) in this locker carry a corroborated proof in the vault ledger (2+ independent witnesses). The rest are here because they are in your owned list or you filed them — which is not the same claim. Nothing is hidden by this chip.' The locker holding Magefist shows n ≥ 1, and the one holding Heart of the Oak shows n ≥ 1. Bone Break and Renewed Black Cleft are counted by NO plate: sunder charms are never assigned to a locker (suggestMule returns null for shared-stash names). A locker holding none of the 14 shows a dimmed '⚖ 0' (present, not absent). On the phone NO plate has a ⚖ chip at all.

**❌ Fail looks like:** A '⚖ 0' on the public site (a claim made from a failed fetch). The chip absent on your console while the eagle row is ✓ (then relaunch once; the ask is made once per load and retried only after a failure). n = 0 on the locker that visibly holds Magefist: the board name and the ledger name differ, and exact-name matching missed it. Items hidden or removed by the chip.

**🔎 Debug first:** The eagle row 'the vault can say what it proves'. Then the board's single 4-second ask to the console (_vaultAskProven): a slow console leaves the chip absent until the next render. Then control_app vault_proven_names.

**Cost:** About 3 min, no paid reads.  
**Unknowns:** Which lockers your board files these names into (the board store was not read). If you have never pressed 'register', Magefist may not be filed at all, and then every chip may read '⚖ 0'.  
**Read from:** bible.html:_vaultAskProven, suggestMule · tv/control_app.py:vault_proven_names · tv/console_doctor.py:_check_the_vault_can_say_what_it_proves

---

## 2 · Chronicle, grail tallies and inbox

Includes #53 (magic/rare vocabulary) and #25 (CHOOSE IN INBOX). Baseline on 2026-09-25 (console v3504, read-only): sets 134/135, uniques 309/403, runewords 99/99. The cross-reference finds 363 of 363 proposed names already in your chronicle. WAITING ON YOU: 0. The shadow gate is answered 'Keep it as it is' (asked again after 25 Oct). 'a fresh remaining page' reads NOT MEASURED.

<a id="mr-01"></a>
### MR-01 — #53 end to end: a stash tooltip read tags magic, rare, grail, base and unknown names correctly (seen once)

**Proves:** #53 / v3364 end to end on a new recording: reel → vault reader → name fold → affix lexicon → result.unsure[].vocab. Includes the edge case that decides it: a unique whose name parses like a rare must come back GRAIL.  
**Setup:** Console on v3504 or later, TV DIABLO window open. Choose items that are physically in your stash and NOT already in the vault's remembered lists: the 43 UNSURE names and 14 OWNED names in the current proposal (see the VAULT ACCUMULATOR). Those are already remembered, so any new recording is their second look and grounds them. Do the whole pass in ONE Mini recording. Inside one 120 s recording a second hover adds sightings but not a second look: a new look inside one recording needs a 3-minute gap between runs. A SECOND recording is a second look at any time gap, and it would ground the item into OWNED, where no tag is kept.

**Items:**
- Raven Claw (unique Long Bow): THE discriminator. Without the roster the lexicon parses it RARE ('raven + claw'); with the roster it must be GRAIL. 38 banked chronicle sightings, so you have had one. Alternatives with the same property: Skull Splitter, Death Cleaver, Rune Master (RARE-shaped), Crown of Ages (MAGIC-shaped).
- Sharp Grand Charm of Vita / Lion Branded Grand Charm of Vita / Shimmering Small Charm: magic charms with a prefix (and suffix); they prove the prefix+base+suffix parse, including a two-word prefix. Any magic charm you own works, as long as its exact name is not in your current UNSURE/OWNED lists (which already hold e.g. 'Grand Charm of Vita', 'Chaotic Grand Charm of Greed').
- A rare ring such as Rune Loop, or a rare helm such as Dread Visage: proves the rarePrefix+rareSuffix parse. Use whatever rare you own. Avoid Blood Gyre, Bone Visor, Death Loop and Dread Grasp, which are already remembered.
- Sigon's Visor (Sigon's Complete Steel helm), or any bare-named set piece: proves the vault fold turns the bare name into the suffixed roster name ('Sigon's Visor (helm)') before tagging, so a set piece reads GRAIL, not UNKNOWN.
- Monarch (white base): the BASE control. It is not in your remembered list; Sacred Rondache is, so it was dropped.
- Any rare amulet whose name ends in 'Scarab' other than Storm Scarab (e.g. Rune Scarab, Doom Scarab): the UNKNOWN control. It must stay UNKNOWN, never guessed into a lane. Storm Scarab was dropped because it is already remembered and would ground.

**Steps:**
1. Console TV·D tab, zone 'Ⅲ THE RECORD', card VAULT ACCUMULATOR. Note the counts in '👁 UNSURE · seen once (N)' and '🏦 OWNED · corroborated (M)' (43 and 14 on 2026-09-25).
2. In game, open the stash tab holding the chosen items. On the ⏱ Mini focus row, click 'stash' so it is lit (a focus you did not choose is not trusted by the sweep). Then press ⏱ Mini (120 s, stops itself).
3. Hover each chosen item until its tooltip is fully painted (about 1-2 s), then move on.
4. Let the Mini stop by itself so the reel seals. Do not start a second Mini on the same items.
5. VAULT ACCUMULATOR: press 'price the sweep' (free, no model call) and read the estimate. Then either wait for the vault watchdog to read the reel on its own, or press 'run it for real'.
6. When the card shows 'this vault proposal was made just now', read the UNSURE column.
7. Read the tags: GET /api/vault_sweep, then for each chosen name read result.unsure[i].vocab and .vocabWhy.

**✅ Expect:** Screen: the card shows 'this vault proposal was made just now'. '👁 UNSURE · seen once' grows by the number of new names. '🏦 OWNED · corroborated' stays at 14, because it is the ledger added up over every sweep and nothing new grounded. Each new UNSURE row reads: the bold name; then 'stash · conf 0.xx · N witness(es)', where N counts SIGHTINGS, not looks (your Horadric Cube reads '20 witnesses' while still unsure); then '👁 AI saw it <age>'; then the why line '<name> in stash — only 1 independent look (…) — needs 2 …'. No MAGIC/RARE word appears anywhere on screen; that is expected, since no renderer shows vocab. API (the actual proof), pre-computed 2026-09-25 with the shipped fold and classifier on this tree: 'Sharp Grand Charm of Vita' MAGIC 'sharp + grand charm + of vita'; 'Shimmering Small Charm' MAGIC 'shimmering + small charm + -'; 'Lion Branded Grand Charm of Vita' MAGIC 'lion branded + grand charm + of vita'; a rare ring such as 'Rune Loop' RARE 'rune + loop'; a rare helm such as 'Dread Visage' RARE 'dread + visage'; 'Raven Claw' GRAIL 'on his roster'; a bare set piece 'Sigon's Visor', folded to 'Sigon's Visor (helm)', GRAIL 'on his roster'; a white 'Monarch' BASE 'exact base type'. The UNKNOWN control, a rare amulet ending in 'Scarab' (e.g. 'Rune Scarab', 'Doom Scarab'), reads UNKNOWN 'no parse against the lexicon', because scarab is a rare suffix with no display string.

**❌ Fail looks like:**

- (a) 'Raven Claw' / 'Skull Splitter' / 'Death Cleaver' tagged RARE, or 'Crown of Ages' tagged MAGIC: the roster did not load and the lexicon guessed.
- (b) A magic or rare name tagged UNKNOWN 'AMBIGUOUS…' or 'no parse…': the reader's spelling differs from the tooltip; compare the row's name with the tooltip on the frame.
- (c) vocab null with vocabWhy 'the lexicon module is unavailable', or vocab UNKNOWN with vocabWhy 'the lexicon has never been generated on this machine'.
- (d) A chosen name lands in OWNED after one pass. Either it was already remembered, or two items with the SAME name were read in two recordings: the vault keys by name, so two 'Shimmering Small Charm's are one row.
- (e) The card says the sweep stopped, or shows the sweep's own 'why' text instead of columns. NOT flakes, measured code facts: 'Atma's Scarab', 'Saracen's Chance', 'Cat's Eye' and 'Flame Rift Grand Charm' tag UNKNOWN on this tree. Do not use them as GRAIL controls; if you hover them, record the UNKNOWN as the known defect.

**🔎 Debug first:** GET /api/vault_sweep (result.unsure[].vocab / vocabWhy, result.totals, phase / error). Then tv/affix_lexicon.json, whose 'counts' must be magicPrefix 269 · magicSuffix 298 · rarePrefix 42 · rareSuffix 152 · baseType 690. Then the console log line '⚠ the affix lexicon will not import'. Do not use GET /api/vault_ledger to check vocab: the seen store drops it.

**Cost:** About 5 minutes of your time. Spends paid reads: one read per stash run on the new reel (a lit 'stash' focus replaces the classify call). 'price the sweep' is free and shows the bill first.  
**Unknowns:** The card placement (TV·D tab, 'Ⅲ THE RECORD'; hidden on the Sessions view since v1674) is taken from the markup, not verified on your pixels. Whether the vault watchdog picks up a Mini reel by itself before you press 'run it for real' is UNKNOWN. Whether the reader returns a magic item's full composed name, rather than the base alone, depends on the reader: the 2026-09-19 result shows it does (e.g. 'Chaotic Grand Charm of Greed'), but for a new item that is only a sample. Whether you own each named item is UNKNOWN; any item of the same class that is not already remembered serves.  
**Read from:** tv/vault_retro.py:_vocab_of, _name_folder · tv/affix_lexicon.py:classify, _roster_folded · tv/control_ui.html:_vaultNames, _vaultPaint · tv/control_app.py:vault_sweep_state, vault_seen_save

> **Note:** Same #53 lexicon as VAULT-MAGIC-01, but deliberately avoids names that are already remembered (Storm Scarab, Sacred Rondache), because a second look grounds them and wipes the tag.

<a id="mr-02"></a>
### MR-02 — #53 second look: a magic item grounds to OWNED, and its magic/rare class is dropped on the way

**Proves:** #53, the second half: a magic or rare name grounds to OWNED on a second look, and (by code reading) its magic/rare class is dropped on the way. No fixture covers a magic name.  
**Setup:** Use a magic or rare name already remembered once, if it is still in your stash: 'Grand Charm of Vita' (MAGIC, remembered at conf 0.75), 'Shadow Amulet of the Whale' (MAGIC, conf 0.9), or 'Death Loop' / 'Dread Grasp' (RARE, remembered at conf 0, so the new read must reach 0.55). These came from recordings made between late July and early September and are listed in the 2026-09-19 proposal. The new look must come from a NEW Mini recording. A different recording is a different look at any time gap; the 3-minute rule only applies inside one recording. The vault keys by NAME, so any 'Grand Charm of Vita' you hover corroborates the remembered one. That proves grounding of the name, not of one physical charm.

**Items:**
- Grand Charm of Vita (MAGIC, suffix-only parse '- + grand charm + of vita'): already remembered at conf 0.75, so one look in a new recording should ground it. Any charm of that exact name works.
- Shadow Amulet of the Whale (MAGIC, prefix+base+suffix): a jewellery magic item, remembered at conf 0.9.
- Death Loop (rare ring) / Dread Grasp (rare gloves): the rare side of the same question. Remembered at conf 0, so the new read must reach 0.55.

**Steps:**
1. VAULT ACCUMULATOR: note the item under '👁 UNSURE · seen once' and the register button's count ('register 14 ✓ · from an earlier session' today).
2. Click the 'stash' focus so it is lit, press ⏱ Mini, hover the chosen item once until its tooltip paints, and let the Mini stop by itself.
3. Let the watchdog read the reel, or press 'price the sweep' then 'run it for real'.
4. Read the VAULT ACCUMULATOR columns again.
5. GET /api/vault_sweep: find the name in result.owned and check that it is gone from result.unsure.
6. OPTIONAL WRITE (your call): 'register N ✓' registers ALL N owned rows, not just this one. Then on the board open the Vault's registered panel and find where the name landed.

**✅ Expect:** Grounding (the part that must work): the name leaves '👁 UNSURE · seen once' (43 -> 42) and appears under '🏦 OWNED · corroborated' (14 -> 15). Its row reads 'stash · conf 0.xx · N witnesses', where N is the number of sightings (at least 2). The register button reads 'register 15 ✓'. The OWNED column is the ledger added up over every sweep, so it rises by one. In the API the row is in result.owned. Code-read prediction for the class: that owned row has NO vocab or vocabWhy field. If you register: the name does not appear under '🔮 Magic & Rare', which is fed only by the AI item checker. Code-read prediction: it lands in d2r_owned via toggleOwned's non-grail branch, where ownedPool cannot resolve a magic name, so it shows under '❓ Not recognised' with the tag 'no match'.

**❌ Fail looks like:** Still UNSURE with 1 look: the new sighting came from the same recording as the earlier one, the read confidence stayed under 0.55 (the why line says 'the reader itself was unsure'), or it was read under a different spelling; compare the names. A throw-out suggestion instead: the reader flagged it as junk. A throw-out needs two recordings agreeing at conf ≥ 0.85 and otherwise shows under ⚖ HELD. Against the #53 goal ('the vault needs to know … what is considered HIGH QUALITY'), the predicted loss of the class at grounding is the finding, not a flake.

**🔎 Debug first:** GET /api/vault_sweep (result.owned[].witnesses, result.unsure, result.held, result.accum.added). Then GET /api/vault_ledger (the owned ledger added up over every sweep, and the remembered sightings; free). After a register: the board Vault registered panel's columns, and the apply receipt's skipped / vaulted / unknown lists.

**Cost:** About 3 minutes plus paid reads for the sweep. The optional register writes to your board's vault; it can be undone only from the board.  
**Unknowns:** Whether you still hold any of these remembered items is UNKNOWN. The landing column after a register is a code read (chronicleApply -> toggleOwned else-branch; the vault door tvVaultRegister is skipped because the row has no loc) and was not run. Whether the owned row's count shows '×N' depends on whether the reader returned a count.  
**Read from:** tv/vault_retro.py:_owned_row, apply_payload, _fold_bare_sessions · tv/control_app.py:merge_vault · bible.html:chronicleApply, _mayVault, toggleOwned, aicJudgeApply

> **Note:** Overlaps VAULT-MAGIC-01 (same items, same grounding). Run only one of them.

<a id="ask-25"></a>
### ASK-25 — #25 on your real window: 'CHOOSE IN INBOX →' lands on the question's card, not a black Tools page

**Proves:** #25 / REG-1297 on your real window: 'CHOOSE IN INBOX →' lands on the question's card, not a black Tools page. Part B also proves the open-question card and records your shadow-gate answer again.  
**Setup:** Your own TV DIABLO window (not a browser tab). The board must have finished booting: wait until the console has been up for about a minute, so the board has fetched the watchdog. In part B, do not press 'Ask me more often': it hands the shadow gate to Claude and changes your ruling.

**Items:** none needed.

**Steps:**
1. Click the version text in the console footer. THE STATE OF THIS CONSOLE opens.
2. Find the section 'ANSWERED BY YOU — held until it lapses or the question changes' and its row 'shadow gate'.
3. Click its button 'you: Keep it as it is · change →' and do nothing else for 5 seconds.
4. Look at where the page landed. Part A ends here: do NOT press the 'change' button that now has focus.
5. PART B (optional, reversible, about 2 min): press 'change' on the landed row. The shadow gate re-opens.
6. Click the footer version again. Under 'WAITING ON YOU', click 'YOUR CALL — CHOOSE IN INBOX →' on the shadow gate row.
7. On the landed card press 'Keep it as it is'.

**✅ Expect:** Before the click, the console row's note reads '“Should the console ask you before it ticks a grail item by itself?” · Fri 25 Sept, 11:49 · asked again after 25 Oct, or sooner if the question changes'. The month may print 'Sep' on an engine with older locale data. Part A: the state window closes and the Tools tab opens with the Inbox card expanded. Its header reads '🦅 waiting-on-you: none — the watchdog measured …'. Below it is '✓ ANSWERED BY YOU — 1' and the row 'shadow gate — “Should the console ask you before it ticks a grail item by itself?” · you: Keep it as it is (Fri 25 Sept, 11:49) · asked again after 25 Oct, or sooner if the question changes [change]'. That row is vertically centred and flashes its highlight, and keyboard focus is on its 'change' button. No toast. Part B: after 'change', the Inbox header reads '🦅 WAITING ON YOU — 1', followed by '(+N not measured)'. Below it is a card '⚖ YOUR CALL · shadow gate' with 'Should the console ask you before it ticks a grail item by itself?', its why-text, and three buttons: 'Keep it as it is' · 'Ask me more often' · 'Remind me in a week'. The console row now reads 'YOUR CALL — CHOOSE IN INBOX →' with '… · your choices: Keep it as it is · Ask me more often · Remind me in a week'. Clicking it lands on that open card with focus on 'Keep it as it is'. After answering, the row is back under ANSWERED BY YOU with today's time and a lapse date 30 days on.

**❌ Fail looks like:** Your 2026-09-25 picture: the Tools tab with a BLACK body and the scrollbar mid-page, nothing in view, the question only in the pop. Or one of these toasts: 'couldn’t open that question in the inbox — the inbox does not show this question (answered, or no longer asked)' (the board has not painted #ibx-needsyou yet, or its watchdog state is UNKNOWN); 'couldn’t open that question in the inbox — the question is not laid out yet' (the retry budget of 40 × 80 ms ran out); 'couldn’t open that question — the board pane isn’t ready'. In part B, a button that answers 'Not recorded: …' or 'This page is not your console’s own page …' means the board is not the console's own /board page.

**🔎 Debug first:** The toast text names the branch. Then GET /api/status -> eagle.answeredWhat (must list 'shadow gate'), eagle.rows[shadow gate].answered[0] (fp 'shadow-gate:wouldHold', effect 'ruled', until 2026-10-25) and eagle.needsYou. On the board, the Inbox card's '🦅 waiting-on-you' line: 'UNKNOWN …' or 'the watchdog has not looked yet this boot' means d2rOpenAsk had nothing to land on. Then tv/ui_faults.jsonl.

**Cost:** 2 minutes (part A) plus 2 minutes (part B). No paid reads. Part B writes to and then restores your answers store.  
**Unknowns:** The exact clock shown ('11:49') is the answer's stored time in your Mac's timezone; another machine shows a different hour. Whether WebKit reports a zero-size rect at all during the Tools switch (the one mechanism REG-1297 hardened against) is UNKNOWN; this scenario is the first place it can be observed. If the shadow gate's disagreement direction changes before you run this (fp moves off 'wouldHold'), the question re-opens by itself and part A becomes part B.  
**Read from:** tv/control_ui.html:_vxAskRow, _vxAnsweredRow, _hubGoAsk · bible.html:d2rOpenAsk, _eagleNYPaint, _askCardsHtml, _askPost · tv/control_app.py:board_answer · tv/console_doctor.py:_ask_shadow_gate · tv/his_answers.py:HOLD_MS

> **Note:** This is also the backlog item "'Choose in inbox' lands on a blank Tools page". REC-07 and DOCTOR-01 use the same landing.

<a id="untick-01"></a>
### UNTICK-01 — Your standing un-tick against a read whose game page says FOUND: does every door respect it?

**Proves:** The nine-un-tick ruling ('d2r_grailUnfound is USER TRUTH'). Only the inbox-triage door checks it. This checks the cross-reference, the sweep's register button and the routing ledger on your real board.  
**Setup:** Only if the board's F-Uniques tab shows the band '❓ N marked NOT found, by you — your un-tick stands until you tap one'. If the band is absent you have no standing un-tick, and the scenario is N/A. You must NOT create an un-tick to test with: an un-tick deletes that item's found date and sightings, with no redo. Pick one name X from the band. Gravepalm was in the band on 2026-08-11, but the 2026-09-25 cross-reference lists Gravepalm as ALREADY in your chronicle, so it is ticked today and most likely no longer in the band. If X is in the band AND still ticked (both stores at once, seen before for Blood Crescent), every door reads it as 'in chronicle'; then this scenario cannot test the rule, so stop.

**Items:**
- X = a name from your own '❓ marked NOT found' band. Chosen because it is the one case where the game's page (FOUND, with a First Found date) and your ruling (NOT found) disagree, so a door that ignores the ruling becomes visible. Gravepalm (a Diablo drop, 25 banked chronicle sightings) was the eye-confirmed example on 2026-08-11 but reads as ticked on 2026-09-25.

**Steps:**
1. Board, F-Uniques: note the headline '🏆 <have> / 403 found' and the names in the '❓ … marked NOT found, by you' band. Pick X.
2. In game, open the Chronicle to the uniques page where X's row shows its 'First Found:' line. On the ⏱ Mini focus row click 'chronicle · uniques' so it is lit, press Mini (75 s, stops itself), and hold X's row in view for at least 20 s of it.
3. Wait for the chronicle lane to read the reel (autoread), or go to TV·D -> CHRONICLE SWEEP -> 'price the sweep' (free) -> 'run it for real'.
4. Hover the console's '📜 Inbox' pill and read its tooltip. Optionally GET /api/chronicle_crossref and read new.uniques.
5. Board Tools -> Inbox: look for X in the routing ledger and, if it has a row, read its status pill.
6. Do NOT press the CHRONICLE SWEEP register button (it will read 'register 1 ✓' if X is offered as new). Stop and report instead.

**✅ Expect:** Per your ruling: X stays in the band, the F-Uniques headline does not move, and there is no toast. If X has a routing row, its pill reads '⛔ you un-ticked it', counted under 'changed your chronicle', not ticked. The 📜 pill must not present X as 'not in your chronicle yet', and the register button must read 'nothing new to register'.

**❌ Fail looks like:** Predicted by the code read. The 📜 tooltip gains '📜 1 of M read from your reels: not in your chronicle yet · read <age>', GET /api/chronicle_crossref lists X in new.uniques, and the register button reads 'register 1 ✓'. That is because the cross-reference compares only foundLog / owned / setPieces and never d2r_grailUnfound. Pressing it would run chronicle_apply -> toggleOwned, tick X and delete its un-tick record, without asking. Also a FAIL: X leaving the band, or a '🏆 X found!' / 'X DISCOVERED in game' toast (tvChronicleRoute has no un-tick check). On the sweep-only path, X having NO routing row is not a failure: held names reach the board only on register.

**🔎 Debug first:** GET /api/chronicle_crossref (new.uniques, why). Then the board routing ledger row for X (status blocked-unfound vs in-chronicle / accepted). Then F-Uniques band membership (_gUnfoundConflicts reads d2r_grailUnfound filtered to the uniques roster).

**Cost:** About 5 minutes. A chronicle sweep of the new reel spends paid reads ('price the sweep' first). Nothing is written if you stop before register.  
**Unknowns:** Whether your band is empty today (UNKNOWN; the 0-new cross-reference and Gravepalm being ticked suggest it may be). Whether a Mini of a Chronicle page is also handed to the board by a live lane (the ON-AIR session propose) or only by the sweep could not be settled from the code; the scenario reads the surfaces both write.  
**Read from:** bible.html:_gUnfoundConflicts, toggleOwned, kaiChronicleSettledWhy, kaiChroniclePropose, _chronicleApplyInner, tvChronicleRoute · tv/chronicle_crossref.py · tv/control_app.py:chronicle_apply

<a id="hand-01"></a>
### HAND-01 — A hand tick on F-Uniques: every tally moves by one, and the tick banks its own 'hand' witness

**Proves:** #166, both halves: a hand tick moves every tally by exactly one (one denominator, v2714), and the tick banks its own 'hand' witness (v2462). The code predicts the witness half FAILS.  
**Setup:** Wait for the next unique (or the one missing set piece) you find that the board did NOT tick by itself, so F-Uniques still lists it as missing. Before tapping, write down the F-Uniques headline, the '🗂 named cards' line, and your row on THE FLEET card in the console rail.

**Items:**
- The next unique you find that F-Uniques still lists as missing: only a genuinely new tick can move the count and write a hand witness. Any name works; the ▦ All missing / ⚡ Quick wins tabs list candidates.
- Alternative: the one set piece still missing (sets read 134/135). Its hand tick writes under the 'sets' ledger and should move F-Sets to 135/135.

**Steps:**
1. Board -> F-Uniques: note the headline '🏆 <have> / 403 found' and its percent (309 and 76% on 2026-09-25).
2. Tick the item by hand on F-Uniques with its '✓ found it' button (the same toggle you always use).
3. Read the toast, the F-Uniques headline and percent, and the ↩ undo bar.
4. Console: on THE FLEET card in the rail, read your row's sets/uniques/runewords figure after the next beacon (up to a few minutes); it reads 134/309/99 today.
5. GET /api/evidence?name=<exact item name> and read ok, lanes, witnesses and say.

**✅ Expect:** Count half: a toast '🏆 <name> found!' with the sub-line 'the unique chronicle grows'. The headline moves by exactly +1, to '🏆 310 / 403 found'. The percent is FLOORED and stays 76% (310/403 = 76.9%); it reaches 77% only at 311. The 🏠 main tab's collapsed 'Chronicle Progress' section reads '310 / 403 grails owned · 93 to go', and its ring is ROUNDED, so it stays 77% and reaches 78% at 313. The item moves from '▦ All missing' to '✅ Found', and the undo bar offers ↩ for it. After the next beacon, your fleet row reads 134/310/99. A set piece instead moves F-Sets to '🧩 135 / 135 pieces · … sets' at 100%. Witness half (per the ruling): /api/evidence answers ok:true with lanes containing 'manual' and say reading '… read by … manual …'. The `witnesses` field is null for EVERY name on this tree (live: Raven Claw with 38 sightings reads witnesses:null), so the 'hand' tag cannot be seen through this route at all.

**❌ Fail looks like:** Count half: +0, +2, or one surface moving while another does not (the fleet row still reads 309 while the board reads 310, beyond one beacon interval). Witness half (the code predicts this FAIL): /api/evidence returns ok:false 'nothing banked for this name — it was ticked by hand, or before the evidence ledger existed, or it is spelled differently in the ledger', or its lanes carry no 'manual'. The board's tick writes d2r_foundLog and a local d2r_lastTick only. _bank_manual_sighting runs only on POST /api/board_tick with want:true, whose sole UI caller sends want:false. Measured today: 0 manual rows among 324 uniques and 126 sets in your evidence bank.

**🔎 Debug first:** GET /api/evidence?name=<item>. Then GET /api/fleet -> your row's tally.uniques / tally.sets / measuredBy (measured:false, measuredBy null today). Then the board's ↩ undo bar and the '🗂 named cards' line. For a count disagreement, read the doctor row 'a tally agrees with its own ledger verdict' via GET /api/status -> eagle.rows. It is red today about another machine's row, so read its why, not its colour.

**Cost:** 1-2 minutes when the find happens. No paid reads.  
**Unknowns:** Monotonic side note: REG-1296 records your console publishing uniques 312 earlier on 2026-09-25, and GET /api/fleet reads 309 now. Whether that is a real drop is UNKNOWN, so record the pre-tap figure on BOTH the board headline and the fleet row. The stored peak (ledger_peaks.json foundLog 416, 2026-09-03) is too old to flag it. The exact fleet-card rendering of your row is from REG-1296, not your pixels.  
**Read from:** bible.html:grailFoundUni, toggleOwned, _markLastTick, _meter · tv/control_app.py:board_tick, _bank_manual_sighting, evidence_for, grail_tally · tv/chronicle_retro.py:witnesses

<a id="remain-01"></a>
### REMAIN-01 — The Remaining-page question: asked once the board can answer, and 'I filmed one' cannot settle it

**Proves:** REG-1230 / #228: 'a fresh remaining page' asks you only when the saved comparison disagrees. It has never been seen on your screen. Also shows that the answer 'I filmed one' has no reader (predicted by the code).  
**Setup:** The TV DIABLO native window must be OPEN while the sweep finishes: the exact check asks the board embedded in it, and with the window closed it records 'the board did not answer (the board window is not open …)'. In game you need Chronicle -> Sets with the 'Remaining' filter.

**Items:**
- The Chronicle's own Sets -> Remaining page: the only in-game surface that can say 'you do not have that'. With 134/135 on your board it should list 1 piece, and that piece is the ground truth this question is about.

**Steps:**
1. In game: Chronicle -> Sets -> Remaining filter. On the ⏱ Mini focus row click 'chronicle · sets' so it is lit, press Mini (150 s, stops itself), and scroll the whole Remaining list while it runs.
2. With the TV DIABLO window open, let the chronicle lane read the reel, or go to TV·D -> CHRONICLE SWEEP -> 'price the sweep' -> 'run it for real'.
3. Footer version -> THE STATE OF THIS CONSOLE -> WAITING ON YOU.
4. Click 'SOMETHING TO DO — CHOOSE IN INBOX →' on 'a fresh remaining page' and read the card.
5. Answer 'I filmed one'.
6. Come back after 2 hours and open the state panel again.

**✅ Expect:** After the sweep, the CHRONICLE SWEEP card shows the calm line 'ⓘ your board is ahead of the last Remaining page · the page is <N> days old' (35 on 2026-09-25). Below it is 'measured: board 134 found · page 19 missing · roster 135 (134 + 19 = 153)' and 'nothing is held back and nothing here is yours to fix …'. The doctor row moves from NOT MEASURED to WAITING ON YOU. The board inbox shows '🔌 SOMETHING TO DO · a fresh remaining page' with 'Film a new Remaining page so the console can confirm <n> set rows?'. The why-text reads 'Your board has 134 set pieces ticked. The last Remaining page (35 days old) still listed 19 as missing, so <n> of your ticked rows are ones that page called missing - most likely found since it was filmed. … A new Remaining page settles it.' <n> is most likely 18 (the page's 19, minus the one piece still missing). The buttons are 'I filmed one' · 'Remind me in a week' · 'Not needed'. After 'I filmed one', the row moves to ANSWERED BY YOU: 'you: I filmed one · change →', with 'asked again after <today's date>, or sooner if the question changes'. Code prediction after about 2 h: the question returns with the same fingerprint (remaining-page:2026-08-21T10:19:13.811000Z) and the same page date, because nothing reads a filmed Remaining page into the readings folder.

**❌ Fail looks like:** The row is still NOT MEASURED after a sweep with the window open: GET /api/chronicle_sweep -> result.calibration.exact.say names why. The question asks with 'None' in it or with no counts: a REG-1249 regression. After 2 h the same question returns about the same 2026-08-21 page: predicted by the code, and it is the finding (the filmed page was never read). A PASS by intent (a new reading and the question closing) would mean a reader exists that was not found. Not the finding: after 2 h the row reads NOT MEASURED again. That means a later sweep ran with the window closed and overwrote the saved comparison.

**🔎 Debug first:** GET /api/chronicle_sweep -> result.calibration.exact (ok, boardFound, gameMissing, surplus, named, reading.readAt). Then GET /api/status -> eagle.rows['a fresh remaining page'] (state, openAsks[0].fp, answered, unknownCount). Then the readings folder tv/remaining/ (only sets_2026-08-21.json today).

**Cost:** About 5 minutes plus a 2-hour wait. The sweep of the new chronicle reel spends paid reads.  
**Unknowns:** The exact <n> depends on how many of your 134 board pieces the 2026-08-21 page named, which is UNKNOWN until the sweep runs with the window open (18 if the piece still missing is one of the page's 19). Whether a chronicle sweep with no unswept reels recomputes the calibration is UNKNOWN, which is why the scenario films a new reel first.  
**Read from:** tv/console_doctor.py:_remaining_page_reading · tv/control_app.py:_chron_calibration · tv/counter_ledger.py:contradicted · tv/his_answers.py:HOLD_MS

<a id="esc-01"></a>
### ESC-01 — Esc with the Chronicle inbox question up, on your WebKit window: 'no', never quit

**Proves:** REG-1254 on your Mac's WebKit window: Esc with 'Promote ALL N?' up answers 'no' and keeps the inbox open, a second Esc closes the inbox, and the console never quits.  
**Setup:** Hover the console's '📜 Inbox' pill first. Its tooltip must start 'Chronicle · N pending · …' with N ≥ 1. If it reads 'Chronicle ledger · M reads (none pending)', the scenario is N/A: 'Accept ALL pending…' then asks nothing. The pill's NUMBER alone is not enough, because it adds the sweep's new-name count. Under no circumstances press 'Promote all N', which is a grail write. Press Esc at most twice. A third Esc, once the inbox is closed, lands on the empty console page and quits the app by design (v1420).

**Items:** none needed.

**Steps:**
1. Click the '📜 Inbox' pill. The Chronicle inbox opens; note the pending count.
2. Click 'Accept ALL pending…'. An in-page question appears: 'Promote ALL N inbox items to FOUND (chronicle write)? … This cannot be undone from here …' with 'Not now' and 'Promote all N'.
3. Press Esc ONCE and look.
4. If the question is gone and the inbox is still open, press Esc ONCE more and look. If the question is still visible, do NOT press Esc again: click 'Not now'.
5. Stop; never a third Esc. Check that the pending count is unchanged.

**✅ Expect:** After Esc 1: the question card is gone, the Chronicle inbox is still open, and the pending count is unchanged. After Esc 2: the inbox closes, the console stays running with no 'Leaving console…' toast, and the 📜 pill still shows the same pending number.

**❌ Fail looks like:** After Esc 1 the INBOX closed but the question is still on screen with 'Promote all N' armed (the pre-REG-1254 shape). Then click 'Not now'; do not press Esc. Or a 'Leaving console…' toast, or the app closing after Esc 2. Or the pending count dropping (something was promoted).

**🔎 Debug first:** tv/ui_faults.jsonl and the console log around the keypress. The pill tooltip's pending count before and after. If it quit: the console log line for /api/quit (from 'escape-empty-stack').

**Cost:** 1 minute. No paid reads. Nothing is written if you never press the yes button.  
**Unknowns:** Whether the Chronicle inbox holds any pending names today is UNKNOWN from outside the board; the pill tooltip settles it by hand.  
**Read from:** tv/control_ui.html:chAsk, chAcceptAllConfirm, inbox capture Esc listener, empty-page Esc quit · tv/test_escape_answers_the_question_no.py

> **Note:** Same REG-1254 ladder as ESC-02 (Fleet). ESC-02's checker says NOT to run this on your Mac, because one wrong key there promotes your real chronicle and there is no unfind. ESC-01 is the only test of your Mac's WebKit. Your call which one to run.

<a id="have-01"></a>
### HAVE-01 — A read names items you already have, including two tricky spellings: nothing moves, nothing is asked

**Proves:** The 'already have' branch on names that broke before (REG-1274's 'Harlequin Crest (Shako)', the curly apostrophe in Atma's Scarab): nothing moves, nothing is asked, and each item appears once.  
**Setup:** Both items are found on your board (Harlequin Crest via the seed after REG-1274; Atma's Scarab dated 2026-06-19 by the game). Your evidence bank has NO chronicle sighting of Harlequin Crest under any spelling (GET /api/evidence answers ok:false), so this read is its first. Atma's Scarab is already in the cross-reference's 'already' list.

**Items:**
- Harlequin Crest: found, but it lived under the suffixed spelling 'Harlequin Crest (Shako)' until REG-1274, and it has no banked chronicle sighting. The spelling fold is under test here.
- Atma's Scarab: the typographic-apostrophe item (54 banked sightings under both spellings); the curly/straight fold is under test.

**Steps:**
1. Board: note the F-Uniques headline ('🏆 309 / 403 found') and the 📜 pill's tooltip.
2. In game: Chronicle -> Uniques. Find the rows for Harlequin Crest and Atma's Scarab. On the ⏱ Mini focus row click 'chronicle · uniques' so it is lit, press Mini (75 s), and hold each row in view for about 10 s.
3. Let the chronicle lane read the reel (autoread), or go to CHRONICLE SWEEP -> 'price the sweep' -> 'run it for real'.
4. Hover the 📜 Inbox pill; read the tooltip. Read the CHRONICLE SWEEP register button's label.
5. Board Tools -> Inbox: read the routing summary line and look for both names.
6. GET /api/chronicle_crossref: read newCount / alreadyCount. GET /api/evidence?name=Harlequin%20Crest.

**✅ Expect:** The F-Uniques headline is unchanged (309/403 as of 2026-09-25) and there is no toast. The 📜 pill number does not rise, and its tooltip carries '📜 M read from your reels: you already have every one, nothing to register · read <age>'. The sweep chip stays hidden. The CHRONICLE SWEEP button reads 'nothing new to register'. The cross-reference keeps newCount 0 (alreadyCount 363, or more if Atma's Scarab's row is new to it). Harlequin Crest's first-ever sighting is one witness, so the sweep will most likely HOLD it: it will not appear in the cross-reference, and GET /api/evidence for it should now answer ok:true. If either name gets a routing row, its pill reads '✓ in chronicle' ('you already had this one') and it is counted under 'already had — nothing to do', never '⏳ needs you'. Each item appears at most once (no second row for 'Atma's Scarab' vs 'Atma’s Scarab', or for 'Harlequin Crest' vs 'Harlequin Crest (Shako)').

**❌ Fail looks like:** The headline goes +1 (a double count through a second spelling). The tooltip reads '📜 1 of M … not in your chronicle yet', or the button reads 'register 1 ✓', for Harlequin Crest or Atma's Scarab. Two routing rows for one item. A '⏳ needs you' row for either. Not a failure: no routing row at all on the sweep-only path, because held names reach the board only on register.

**🔎 Debug first:** GET /api/chronicle_crossref (new / already lists). Then the CHRONICLE SWEEP held column for Harlequin Crest. Then the board routing ledger rows (status + store). Then GET /api/evidence?name=Harlequin%20Crest (the first banked sighting, and under which spelling).

**Cost:** About 3 minutes plus paid reads if a sweep is run.  
**Unknowns:** Whether a Mini of a Chronicle page is also handed to the board live (the ON-AIR session propose) or only through the sweep is not settled from the code; the scenario reads the surfaces both write.  
**Read from:** bible.html:kaiChroniclePropose, kaiChronicleSettledWhy, kaiChronicleLedger · tv/chronicle_crossref.py:canon · tv/control_app.py:chronicle_crossref_state

<a id="new-01"></a>
### NEW-01 — A read names an item you do NOT have: it ticks by itself (your 'Keep it as it is'), and every tally moves by one

**Proves:** Your shadow-gate ruling ('Keep it as it is') in practice: a grounded new grail name ticks itself, and every tally moves by one. First real check since the REG-1289 per-ledger seal. Also checks a mislabel found by code reading.  
**Setup:** The next unique or set piece you find that F-Uniques / F-Sets lists as missing (94 uniques and 1 set piece were missing on 2026-09-25). Note the board headlines and your fleet row before picking it up.

**Items:**
- Any unique F-Uniques lists as missing (the ⚡ Quick wins tab names low-level ones you can target): only a genuinely missing name exercises the auto-tick branch.
- The single missing set piece (F-Sets shows which): its tick completes sets 135/135, the loudest possible check that F-Sets, the fleet row and the console agree.

**Steps:**
1. Before: F-Uniques '🏆 309 / 403 found' (76%), F-Sets '🧩 134 / 135 pieces …' (99%), your fleet row (134/309/99), and the routing summary line in Tools -> Inbox.
2. Pick it up and identify it in game. If the game prints its discovery line in chat, leave it on screen a moment.
3. Watch for a board toast, then read the F-Uniques (or F-Sets) headline and its '✅ Found' tab.
4. Board Tools -> Inbox: read the routing summary and the item's pill.
5. After the next beacon: your fleet row.
6. If nothing ticked live: film the item's Chronicle row (Mini, focus 'chronicle · uniques'), let the sweep read it, and hover the 📜 pill.

**✅ Expect:** The count moves on every surface: F-Uniques reads '🏆 310 / 403 found' and stays 76% (floored; 77% only at 311). The 🏠 main tab's 'Chronicle Progress' reads '310 / 403 grails owned · 93 to go' with its rounded ring at 77%. The item sits under '✅ Found'. No WAITING ON YOU question. Your fleet row reads 134/310/99 after the next beacon. A set piece moves F-Sets to '🧩 135 / 135 pieces …' at 100%. Which door fired decides the rest. (1) The ON-AIR session propose: triage 'safe-auto-grail' writes foundLog with NO toast. The row's pill reads '✓ ticked', and 'changed your chronicle' rises by one (it counts the last 400 routing rows, so it is not '1'). (2) The TV route (chat DISCOVERED / equipped / vault): a toast '🏆 <name> found!' or '🏆 <name> DISCOVERED in game', sub-line 'the unique chronicle grows'; a set piece gives '🧩 <piece> chronicled!' / 'DISCOVERED in game'. Code-read prediction: its routing row then shows '✓ in chronicle' with the why 'you already had this one', under 'already had — nothing to do', not under 'changed your chronicle'. (3) The sweep path, if neither fired: the tooltip gains '📜 1 of M read from your reels: not in your chronicle yet'. The CHRONICLE SWEEP button reads 'register 1 ✓', and pressing it gives '✓ 1 registered in your chronicle · <M−1> you already had · undo from the board'.

**❌ Fail looks like:** It lands as '⏳ needs you' (held: tier-grail-ungrounded / gateHeld / human-review). That contradicts 'Keep it as it is' only if the read was a clean, grounded name; check the pill's reason. The count moves on the board but your fleet row stays 309 beyond a beacon interval, or the reverse (denominator or relay drift, the REG-1289 class). '⛔ held back by the game’s own missing list' on a set piece found after 2026-08-21: denied() ordered the times wrongly. If door (2) fired and the row reads 'already had — nothing to do', that is the predicted mislabel, a finding and not a flake.

**🔎 Debug first:** The board routing ledger row (status + why) for the item. GET /api/fleet -> your row's tally.uniques / tally.sets / measuredBy. GET /api/chronicle_crossref. GET /api/status -> eagle.rows['a tally agrees with its own ledger verdict'].

**Cost:** 2 minutes at the moment of the find. No paid reads on the live path; the sweep path spends paid reads, and its register writes your board (which is the point here).  
**Unknowns:** Which live door fires depends on what you do in game; the code has at least three, and the toast and routing-row wording differ per door (see expect). The re-labelling of a TV-route row as 'already had' is a code read, not yet seen on your screen.  
**Read from:** bible.html:kaiChronicleTriage, tvChronicleRoute, kaiChronicleLedger, _meter · tv/console_doctor.py:_ask_shadow_gate · tv/control_app.py:grail_tally, chronicle_apply · tv/test_one_chronicle_denominator.py

---

## 3 · TV DIABLO recording and reading

ON AIR / MINI doors, reels, theatre, warm workers, receipts, retention and prune, and the Windows eye. Baseline on 2026-09-25: the newest reel on disk is from 2026-09-15; the ON AIR door has 1 readable reel out of 53; MINI has 0 out of 5; 14.0 GB free. 👁 EYES is on PRIMARY (Grok first). The shadow door and the text eye are OFF by your choice.

<a id="rec-01"></a>
### REC-01 — ON AIR end to end: one real reel, sealed whole, credited to the ON AIR door

**Proves:** The ON AIR door end to end: a real reel sealed whole and credited to ON AIR (v2316/v2687; seal chain v947/v2071/v946). Your ledger shows ON AIR at 1 readable reel out of 53. Credit and seal have only been proven by fixtures.  
**Setup:** Mac. D2R in-game (not the Battle.net launcher), windowed and visible, in a private solo game in town beside the stash. The open stash page holds Dwarf Star, Raven Frost and REC-03's items. Move Goblin Toe from the stash to the inventory (for REC-07). In TV DIABLO, press ⟲ relaunch in the utility row twice: the first press changes it to '⟲ sure? the window will reopen'. On TV·D, open ⚙ ADVANCED → 👁 WHICH EYES READ. The switch reads PRIMARY today. Press OFF (Claude only) for this session, and press PRIMARY again after End Session. Before On Air, open the console's /api/status (port 17772) in a browser tab and note captureDoors.onair. Today it reads opened 62, refused 5, filmed 1, blank 52, judged 53. Also note prune: passes 0.

**Items:**
- Dwarf Star: a unique Ring already in your vault sightings (stash lane). Your sightings also hold a bare 'Ring' row (a base-name read), so a receipt that says 'Dwarf Star' proves the tooltip was named, not the base.
- Raven Frost: a second unique Ring in your stash sightings. Two distinct receipts for two rings on the same base rule out a sticky echo of one name.

**Steps:**
1. Press ▶ On Air. The console moves to the TV·D cockpit by itself.
2. Check the capture pill and the On Air button label.
3. For REC-08: keep every panel closed and stand completely still in town for about 60 s.
4. Click the stash chest to open it. Within about 2 s, move the cursor onto Dwarf Star so its tooltip shows. Then keep the mouse completely still for 6 s. A read fires once the screen has been still for about 4 s, and your lurking text eye is off, so opening the panel and then going still is what triggers a read.
5. Click into the game window. Close the stash with its in-game ✕. Never press Esc while the console window has focus. Reopen the stash, move onto Raven Frost and hold still for 6 s.
6. Now do the steps from REC-03 and REC-07. Keep recording until at least 6-7 minutes in total, for REC-08. Then press End Session.
7. Reload the /api/status tab and read captureDoors.onair.
8. In Finder, open tv/frames/hist and find the newest reel_s_<t0>_<n> folder. Open its index.json.
9. Press 🦅 eagle. It runs every row, including the hourly ones, and can take a minute or two. Read these rows: 'footage has a reel', 'reel population', 'unattended reel' and 'engines corroborate'.
10. Set 👁 EYES back to PRIMARY.

**✅ Expect:**

While live: the On Air button reads 'End Session'. The capture pill reads '🎯 Locked · Diablo II'. There is no NO EYE, D2R-missing or DISK FULL banner. READ BLIND may show while nothing new is on screen, and should clear once a read lands. With EYES on OFF, AI READS · live shows '🔴 read Dwarf Star · STASH · …' and '🔴 read Raven Frost · STASH · …' within about 40 s of each settle. Each row carries '🗄 registered', because the scene is stash.

On End Session: the label goes 'ending…' → 'closing…'. The toast says 'session saved · off air'. The button returns to 'On Air'.

captureDoors.onair afterwards: opened 63, refused 5, filmed 2, blank 52, judged 54, and say reads '2 of 54 reels held readable film · Wilson floor 0.010'. The Wilson floor is computed from tv/confidence.wilson_lower(2,54).

The new folder reel_s_<t0>_<n> exists, where t0 is the moment the agent started, in epoch ms. Its index.json holds sessionId s_<t0>_<n>, blankPass true, and an n equal to its f_*.jpg count. n + status.prune.framesDropped ≈ seconds on air (1 footage frame per second), minus warm-up.

Eagle rows: 'footage has a reel' still says 1 frame belongs to no reel, not more. 'reel population' reads 20 reel(s) on disk (19 today). 'unattended reel' reads 'nothing is recording'. 'engines corroborate' is not red on door-opens-are-counted.

**❌ Fail looks like:**

- The pill stays '⏸ waiting · D2R', or the banner reads 'NO EYE — waiting for D2R pin (not filming desktop)' or the D2R-missing message. There is no film.
- A receipt reads 'Ring' instead of Dwarf Star or Raven Frost. The bare 'Ring' row already in your vault sightings is this exact failure.
- tv/control_app.log prints '🚨 End Session: force-killing the agent … NO index.json' or '🩹 rebuilt missing index'. Note that the toast is NOT a witness. stop_agent returns sessionSaved true on the forced path too, so the toast reads 'session saved · off air' even when the seal was cut short.
- There is no new reel folder.
- captureDoors.onair judged stays at 53 (the credit never ran), or blank becomes 53 while receipts named both rings (the credit read the wrong session).
- 'footage has a reel' counts more loose frames than before.
- The agent banner line 'film ON/OFF' in control_agent.log is NOT a witness. tv_diablo.py:6841 defaults TV_FILM to 0, while the film thread (:2221) defaults it to 1. The last banner on your log printed 'film OFF'. Count frames instead.

**🔎 Debug first:** /api/status → captureDoors.onair, screenRecOk, captureTarget, and the agent's footageWhy (for example 'no D2R window — not recording (N frame(s) skipped)'). Store: tv/capture_doors.json. Its '_lastDoor' key should be gone once credited. tv/control_app.log: '⏳ End Session: seal in flight…' and '🔁 after the session: …'. tv/control_agent.log: '⚠ screencapture failed'. If loose frames grew, check the eagle row 'footage has a reel', then run python3 tv/orphan_fold.py (it only plans; it refuses to move anything without --apply --yes).

**Cost:** About 12 minutes of your time, because REC-03, REC-07 and REC-08 ride along. With EYES on OFF it spends paid Claude subscription reads: 2 here, plus 1 boot warm-up ping, plus any second-eye verify asks. The eagle 'subscription' row counts them. On PRIMARY these would be Grok subscription reads instead (see the /api/g5_status budget). The after-session vault-lane nudge may also read the new reel's stash panels, which is paid, and the count is UNKNOWN.  
**Unknowns:** The exact n depends on warm-up and prune drops. Whether a settle fires with the tooltip in view depends on motion thresholds that were not measured by hand. If a panel open yields no read, close the stash, reopen it and try again. Whether the reader names both rings is the thing being measured. Which 'reel population' bucket the new reel lands in ('he sees' or 'still owed') is UNKNOWN. Only the total (20) is predictable. With EYES left on PRIMARY, read timing is UNKNOWN, because Grok's own timeout is 140 s.  
**Read from:** tv/control_app.py:start_agent, after_session_ended, capture_door_credit, stop_agent · tv/confidence.py:wilson_lower · tv/tv_diablo.py:claude_read · tv/g5_grok_eyes.py:mode_intent · tv/control_ui.html:cutFeed, _receiptRow · tv/console_doctor.py:_check_footage_belongs_to_a_reel

> **Note:** REC-03, REC-07 and REC-08 run inside this same session. Read all four before you press On Air.

<a id="rec-02"></a>
### REC-02 — Reel 39108 leaves the newest-8 shield and must be HELD, never tombstoned (REG-1277)

**Proves:** REG-1277 on your real shelf: reel …39108, the exact shape that deleted 13 reels on 2026-09-10, must be HELD and never tombstoned once it leaves the newest-8 shield. A wrong answer is permanent.  
**Setup:** Before REC-01, open the console's /api/reel_story in a browser tab and find reel_s_…_39108. Today it reads tag 'recent', stage 'releasable', held true, and the why 'one of the 8 most recent — kept so a re-sweep always has real footage'. Then run REC-01, so that one new reel seals. The retention pass runs at console boot and every 15 minutes. REG-1277's reels were deleted one second after a relaunch, so REC-04's ⟲ relaunch is itself a decision point.

**Items:**
- No game item. The subject is reel_s_…_39108. It is the one reel on your shelf that has the REG-1277 shape (seal rows 0, durable only through live witnesses) and is exactly one new reel away from losing its shield.

**Steps:**
1. Right after REC-01's End Session, open tv/control_app.log and read the '🔁 after the session: …' line.
2. Reload /api/reel_story and find reel_s_…_39108.
3. Wait for the next retention pass. That is at most 15 minutes, or sooner if REC-04's relaunch comes first.
4. Reload /api/status and read retention.say, retention.eligible and retention.removed.
5. Press 🦅 eagle and read the rows 'end routes reachable' and 'disk headroom'.
6. In Finder, check that tv/frames/hist/reel_s_…_39108 still holds its 268 f_*.jpg files.

**✅ Expect:**

The after-session line reads '… NOTHING is safe to delete yet — and that is an answer, not a failure. every reel is recent, unread, or still owed to a lane.'

The reel_story row for 39108 reads tag 'panels-never-banked', stage 'banked', held true, and the why 'a FULL survey found panel frames here and the vault ledger holds NO row from this reel — its stash rows have never been extracted, so deleting it destroys the only copy. A seal is not an extraction.'

retention.eligible is 0 and removed is []. retention.say starts '<N>GB free — above the 8GB floor. Nothing is eligible to free.'

Eagle 'end routes reachable' does NOT start with 'the reel deleter would RELEASE'. It still names reel_s_…_39108 with 268 unread panel frames. Today it is named as 'Biggest'. It stays the biggest unless the new REC-01 reel, once surveyed, holds more unread panel frames.

Eagle 'disk headroom' reads '<free>GB free — your last N reel(s) averaged X GB/hour, so this is about H hour(s) of recording · footage is F GB', with F up from today's 2.4 GB by about the size of the new reel.

The folder is still there, and tv/reel_tombstones.json has no …_39108 entry.

If REC-05 also ran (a second new reel), reel_s_…_41906 leaves the shield too. It is NOT a test fixture: the fixture scan counts only reel_s_ ids in executable test code, and 41906 appears only in a docstring. It already reads 'recent', and the chain checks 'recent' after 'test-fixture'. Its full survey found 0 panels, so it counts as proven empty. It has no vault seal and no chronicle evidence. By the code it becomes 'eligible', and the next pass removes it: the log line reads '🗃 freed 3 MB by removing 1 reel(s) that had already given up their information; tombstones written to …'. That is correct under your ruling, and it is permanent.

**❌ Fail looks like:**

- The 39108 row reads tag 'eligible'.
- retention.removed or the after-session plan names reel_s_…_39108. A '1 reel(s) may go' that names only 41906 after REC-05 is expected, not a failure.
- Eagle 'end routes reachable' reads 'the reel deleter would RELEASE 1 reel(s) every end-route door refuses (reel_s_…_39108)'.
- The 39108 folder is gone, or tv/reel_tombstones.json gains a …_39108 entry.

A release of 39108 is legitimate only if tv/vault_swept.json showed rows > 0 (or examinedEmpty true) for s_…_39108 BEFORE it happened. That would mean a re-sweep really extracted it. Check that before calling it a regression.

**🔎 Debug first:** The /api/reel_story row (tag, why). python3 tv/river_walk.py reel_s_…_39108 (read-only). Stores: tv/vault_swept.json key s_…_39108 (today rows 0, extractedWhy 'nothing was taken'), tv/retro_triage.json (full true, panels 268, kinds stash only), tv/chronicle_swept.json (pages 0), tv/vault_seen.json (the two live witnesses), tv/reel_tombstones.json. Log: tv/control_app.log.

**Cost:** 3 minutes of your time plus up to 15 minutes of waiting. No paid reads of its own.  
**Unknowns:** The expected tag 'panels-never-banked' is derived from the code and your stores, and has not been observed yet. If the vault lane re-sweeps 39108 with a newer prompt and banks rows first, a release becomes correct behaviour. Whether 39108 stays 'Biggest' on the end-routes row depends on the new reel's surveyed panel count.  
**Read from:** tv/reel_retention.py:_panels_never_banked, _proven_empty, KEEP_RECENT · tv/frame_authority.py:seal_releases_frames, test_referenced_reels · tv/control_app.py:_retention_loop · tv/end_routes.py:deleter_disagrees · tv/console_doctor.py:_check_every_reel_can_still_reach_an_end_route

> **Note:** Every ON AIR or Mini recording in this catalogue seals a new reel. The FIRST new reel of the testing phase exposes …39108, whichever scenario made it. Run this right after that first reel.

<a id="rec-03"></a>
### REC-03 — REG-1300 on real workers: the OCR worker on every read, and the Claude vision worker (EYES on OFF) across a worker respawn

**Proves:** REG-1300 on real workers: the OCR worker answers on every read, and the Claude vision worker survives its 8-turn respawn. Proven only against a fake worker; the eagle row only greps source.  
**Setup:** Rides REC-01's ON AIR, with 👁 EYES on OFF. One stash page holds 9 or more distinct identified items. Click the '🧾 AI READS' tag once so it reads '· thoughts'. The cycle is live → thoughts → story → log.

**Items:**
- Dwarf Star and Raven Frost: the same base (Ring), so each is new text and a separate read.
- War Traveler: #60's real-read item (read as quality=unique from reel 39108).
- Goldwrap, Magefist, Gheed's Fortune, Goblin Toe: uniques in your stash-lane vault sightings, each with a short, distinct tooltip.
- Heart of the Oak and Enigma: runewords (both in your stash sightings) whose gold name line sits above the base, a second naming shape.
- Nine distinct names crosses the 8-turn worker respawn even with the boot ping counted. Distinct text matters so each panel open is a fresh settle, not a repeat of the same view.

**Steps:**
1. For each item in turn: click into the game window and close the stash with its in-game ✕ (never press Esc while the console has focus). Reopen the stash, move onto the item within about 2 s, and hold still for 6 s. Items: Dwarf Star, Raven Frost, War Traveler, Goldwrap, Magefist, Gheed's Fortune, Goblin Toe, Heart of the Oak, Enigma (any 9 or more on one page).
2. After each settle, watch AI READS · thoughts for a '⚡ocr … ms · N name(s) — …' line and a read line ending '[warm sonnet N.Ns] · ocr NNms'.
3. Watch the '🔴 Live Eye' status: it goes from 'thinking Ns' back to 'watching'.
4. After End Session, count the session's read modes from the journal (read-only): grep 's_<t0>_<n>' tv/sessions.jsonl | grep -o '"mode": "[a-z0-9-]*"' | sort | uniq -c
5. Press 🦅 eagle and read the rows 'subscription' and 'a worker read has a deadline'.

**✅ Expect:**

Each settle gives '⚡ocr <tens to ~200>ms · N name(s) — <names>' (raw N), which means the OCR worker answered through the bounded write. Within about 35 s a read line follows, ending '[warm sonnet N.Ns] · ocr NNms'.

In thoughts, zero lines read 'vision worker died (timeout/stream end) — one-shot for this read, re-warming behind it'.

In the journal, every deep row of the session is mode 'warm', including the reads after the respawn. There are no 'oneshot' rows, and no 'g5-primary' rows (if there are, EYES was not OFF).

No 'VISION SLOW — read in flight Ns' banner appears (it shows past 45 s), and no '🐢 THROTTLED'.

The 'subscription' row's reads-this-hour rises by at least the number of reads (the boot ping and verify asks are billed too).

**❌ Fail looks like:**

- A journal row with mode 'oneshot', or 'vision worker died …' in thoughts. That means a warm write or read did not land, and the REG-1300 bury path or the 35 s bound fired.
- No '⚡ocr' lines at all, and read lines without '· ocr NNms': the OCR worker's write never lands.
- The 🔴 Live Eye stuck on 'thinking 30s' or more: the hang shape from before the fix.
- Many ocr_mac processes in Activity Monitor: a respawn per frame.

**🔎 Debug first:** The journal mode count (step 4) is the durable verdict. Activity Monitor should show exactly one ocr_mac and one claude child under tv_diablo.py. Note that '[warm', '[oneshot' and 'vision worker died' are NOT in tv/control_agent.log. That log prints only '[sonnet]'-style tags, and the AI READS · log view shows only its last 4 lines, with no scrolling. Only '⚡ ocr' lines land in that log. Do NOT use the eagle row 'a worker read has a deadline' as the verdict: it greps source and stays green whatever a live worker does.

**Cost:** Rides REC-01 (about 6 extra minutes). About 9-12 paid Claude subscription reads, plus verify asks.  
**Unknowns:** The branch where the worker ignores its input cannot be produced by hand. OCR ms figures vary by frame. A read line in thoughts can be cut at 120 characters before its '[warm …]' tag, so use the journal count. If a panel open yields no read (a repeat of the same view), move off the page and back, then note it as a missed settle, not a worker fault.  
**Read from:** tv/tv_diablo.py:_pipe_write_by, _bury_worker, VisionWorker.ask, OcrWorker.read, WORKER_MAX_TURNS · tv/console_doctor.py:_check_a_worker_read_has_a_deadline, _check_subscription_burn

<a id="rec-04"></a>
### REC-04 — Theatre after a relaunch: first open is prompt, switching views closes it, ✕ CLOSE is there, no 1970 beat, card = dossier = disk

**Proves:** REG-1284 (the first theatre open after a restart is prompt), REG-1286 / #172 (switching views closes the theatre), REG-1255 (no 1970 beat), and whether ✕ CLOSE is visible on the film stage.  
**Setup:** REC-01's reel is sealed. Press ⟲ relaunch twice and wait for the window to reopen on Sessions. Do step 1 within about 10 s of it reappearing, while the boot warm-up of the fixture scan may still be running.

**Items:**
- No game item. REC-01's reel, specifically its Dwarf Star tooltip beat. Scrubbing to it proves the film and the read landed on the same moment.

**Steps:**
1. Click the 'TV·D' header tab. In 🗂 HISTORY, press 'see all →'. This opens the theatre (the first open after the relaunch) and then the shelf. Note how long it takes for the film and shelf to appear.
2. On the shelf, find REC-01's card and read its line and date. Tap it to open the dossier and read its 'frames' tile. Then press '▶ Open in Theatre'.
3. Look for '✕ CLOSE' on the stage header. Scrub to the first beat and read its time. Then scrub to the Dwarf Star hover and read the beat card.
4. Click the 'Vault' header tab.
5. Reopen the theatre the same way (TV·D → 'see all →' → card → ▶ Open in Theatre). Then click the 'Sessions' header tab.
6. Reopen it again, then click the 'TV·D' header tab, which is the tab already showing.
7. Press ✕ CLOSE.

**✅ Expect:**

The shelf opens without a pause of many seconds (REG-1284 measured about 0.08 s cold on a scratch console; the page gives up at 8 s). Your exact time is UNKNOWN.

REC-01's shelf card shows its real date and a line '📹 N frames · full video'. N equals the dossier's 'frames' tile and index.json n (both are counted from the reel folder).

'✕ CLOSE' is visible on the stage header.

The first beat carries today's time, not a 1970 date. The Dwarf Star beat names Dwarf Star over the tooltip frame.

Clicking Vault closes the theatre, and the Vault view shows with no dark film stage over it.

Clicking Sessions closes it, and the hub shows.

Clicking TV·D (the same tab) leaves it open.

✕ CLOSE closes it.

**❌ Fail looks like:**

- On the first open, the stage appears and then vanishes with nothing played. The page writes '🎞 could not reach the console …' into the theatre caption, but the same branch hides the theatre, so that caption is not visible. The witness is a ui_fault of kind 'theatre-open-no-sessions'.
- A black stage.
- A dark film stage covering the Vault: #172's original report.
- The same-tab TV·D click closes it.
- A 1970 first beat, or a card whose duration runs to days or years.
- The card, dossier and index.json frame counts disagree.

**🔎 Debug first:** First, the eagle rows 'running code matches disk' and 'window runs the document on disk' must read ok. If they do not, the window is still the old page without REG-1286. Then check the eagle rows 'console UI faults' and 'fault evidence' for a ui_fault of kind theatre-open-no-sessions. Then GET /api/sessions, which should answer in under 1 s cold. Then the eagle row 'stage shows the dom'.

**Cost:** About 6 minutes. No paid reads.  
**Unknowns:** The Vault header tab wears a 🔒 lock chip. By the code, the view still opens, but what it paints while locked belongs to the vault area. The dossier overlay sits above the header, so close it (or press ▶ Open in Theatre, which hides it) before any header click.  
**Read from:** tv/control_ui.html:thOpen, thClose, header-tab close (#172) · tv/control_app.py:/api/sessions, test_referenced_reels_nowait

<a id="rec-05"></a>
### REC-05 — MINI door: a bounded stash reel that stops itself, is credited to MINI, and says what focus it declared

**Proves:** The MINI door: a bounded stash reel that stops itself, is credited to MINI (0 of 5 readable so far), and stamps its focus. Also exposes a code finding: focusChosen is always true.  
**Setup:** D2R in-game at the open stash, with War Traveler and Gheed's Fortune on the page. Not on air. 👁 EYES on OFF if you want Claude-worker reads. Note captureDoors.mini in /api/status. ⚠ Decide first: this is the second new reel of the day. It pushes reel_s_…_41906 (19 frames, 0 panels, proven empty) out of the newest-8 shield, and by the code the next retention pass tombstones it permanently (see REC-02).

**Items:**
- War Traveler: #60's real-read unique (Battle Boots base), in your stash sightings. A named read inside the 120 s window is what turns the MINI's 'blank' into 'filmed'.
- Gheed's Fortune: a unique Grand Charm in your stash sightings. Its tooltip is small, which gives a second chance at a read inside the bound.

**Steps:**
1. On TV·D, do NOT touch the Mini focus chips. The Mini sub should read 'stash · 120s, stops itself'. Press ⏱ Mini.
2. Read the toast and the On Air button.
3. Click into the game window and close the stash with its in-game ✕ (no Esc while the console has focus). Reopen it, move onto War Traveler within about 2 s and hold still for 6 s. Do the same for Gheed's Fortune.
4. Press nothing else. Let it count down to 0.
5. Open the console's /api/mini and /api/status (captureDoors.mini).
6. Open the new reel folder's index.json in a text editor.

**✅ Expect:**

The toast reads '⏱ MINI — 120s on stash · it stops itself', and the console moves to TV·D. The Mini sub reads 'recording · Ns left' and counts down. The On Air button reads 'End Session', with the sub 'MINI holds the capture · Ns left', and does not offer a second capture.

At 0: no '⏱ MINI recorded NOTHING — 0 frames…' toast appears, and the On Air button returns to 'On Air'.

/api/mini: running false, sealedBy 'deadline', sealedFrames about 100-120.

captureDoors.mini: opened 6, refused 197, filmed 1, blank 5, judged 6, and say reads '1 of 6 reels held readable film · Wilson floor 0.030'.

index.json has 'focus': 'stash', 'mini': true and 'miniSeconds': 120. By the code it will ALSO have 'focusChosen': true, even though you never picked it. That contradicts v1783's rule that a preselected default is not a choice. Record it as a finding for the queue, not as a pass.

**❌ Fail looks like:**

- The 'MINI recorded NOTHING' toast, or the sub '⚠ sealed with 0 frames — nothing was captured'.
- sealedBy 'start-failed', or the MINI running past 120 s.
- On Air offering a second live capture while the MINI counts down.
- captureDoors.mini blank goes to 6 while receipts named War Traveler.
- No focus key in index.json.

**🔎 Debug first:** /api/mini (sealedBy, sealedFrames, framesSeen, sid). Store: tv/capture_doors.json. tv/control_agent.log banner line '⏱ MINI CAPTURE — 120s, focus=stash'. tv/control_app.log.

**Cost:** About 4 minutes. About 2-4 paid live reads (Claude with EYES on OFF, Grok on PRIMARY), plus the after-session vault nudge. Side effect: reel 41906 is released at the next retention pass.  
**Unknowns:** Whether a read lands inside 120 s is the measurement. Whether you want focusChosen to stay true for the preselected chip is YOUR ruling. The code's current answer is known (true).  
**Read from:** tv/control_app.py:mini_start, _mini_focus, start_agent, _mini_seal, _mini_watchdog · tv/tv_diablo.py:MINI_FOCUS_CHOSEN · tv/vault_retro.py:_declared_surface

> **Note:** ⚠ Permanent side effect: the second new reel of the phase releases reel …41906 at the next retention pass (see REC-02).

<a id="rec-06"></a>
### REC-06 — Windows eye: held with no D2R (a browser naming the game is never filmed), locked with D2R; frames decode; disk is measured

**Proves:** On Windows: REG-1250 (an unpinned eye never films the desktop or a browser), REG-1247 (free disk measured with shutil), REG-1260 (Pillow decodes a frame). All three shipped in v3500; none has been seen on a real Windows ON AIR.  
**Setup:** Your Windows console with D2R installed, on footer v3500 or later. D2R fully closed (no D2R.exe in Task Manager). A Chrome window in front whose ACTIVE tab title contains 'Diablo II' (for example Blizzard's Diablo II: Resurrected page). The capture reads the window title, which comes from the active tab. Optionally, a SECOND Chrome window whose active tab is GeForce NOW. TV_CAPTURE must be unset (auto), because in 'window' mode the held branch is never reached.

**Items:**
- A named unique in THAT machine's stash. War Traveler would allow a comparison with the Mac, but whether that account holds it is UNKNOWN.
- A Chrome window whose active-tab title names 'Diablo II': the discriminating non-item. It matches the game regex but names no streaming service, so it must be neither pinned nor filmed.

**Steps:**
1. Press 🦅 eagle and read the rows 'this machine can decode a frame' and 'disk headroom'. In a terminal, run python3 tv\river.py (an instrument that prints every joint and always exits 0) and read the 'disk' joint.
2. Press On Air with D2R closed and leave it for 60 s, keeping the Chrome window in front.
3. Read the capture pill and the banner. Open tv\frames\hist and look for new f_*.jpg files.
4. Press End Session.
5. Start D2R and enter a game at the stash. Press On Air, open the stash on a named unique and hold still for 6 s. After 2 minutes, press End Session.
6. Run python3 tv\river.py again and press 🦅 eagle.

**✅ Expect:**

Eagle before: 'this machine decodes a frame: Pillow <ver> round-tripped a BMP (the format the Windows capture writes) pixel for pixel'.

river.py: the 'disk' joint's crossed column is a GB figure, never '?'. The joint's state can still be UNKNOWN when the prune joint above it is unknown, so read the figure, not the state.

With D2R closed: the pill reads '⏸ waiting · D2R'. The banner reads the D2R-missing message or 'NO EYE — waiting for D2R.exe window pin (not filming desktop)'. status.captureTarget.label is 'eye held - no game window and no D2R.exe, so the desktop is never filmed'. If the GeForce NOW window is open, the label adds '; a cloud window is open but its title does not name the game: <proc> '<title>''. ZERO new f_*.jpg files: the Chrome page is never filmed.

With D2R running: the pill reads '🎯 Locked · Diablo II', frames arrive, a '🔴 read <name>' receipt lands, and a reel folder seals.

'disk headroom' shows a GB figure. That row always used shutil, so it is not a REG-1247 witness; river.py's disk joint is.

**❌ Fail looks like:**

- Any f_*.jpg while D2R was closed: the desktop or Chrome was filmed, which is the REG-1250 regression.
- The label reads 'D2R alive - full virtual fallback', or the pill reads Locked with no D2R.
- 'Pillow will not import…' or 'could not decode a 4x3 BMP'.
- river.py's disk joint prints '?' with an error in its why.

**🔎 Debug first:** status.captureTarget and captureProc (LINKED / DEAD / RESTARTED). tv\control_agent.log for capture_win.ps1's own lines ('  eye held - …', '  full virtual screen (no D2R pin)'). tv\frames\cap_target.txt (mode|label). The eagle row 'this machine can decode a frame', which quotes console_doctor.PILLOW_BOOT.

**Cost:** About 12 minutes at the Windows machine. About 1-3 paid reads, none during the held minute.  
**Unknowns:** Which Windows machine has D2R installed is UNKNOWN, and so are that machine's EYES setting and stash. GeForce NOW's real window title is UNKNOWN. The label only gains the near-miss clause if that title contains 'geforce now' and no game word. The fullscreen fallback (local D2R.exe alive, no pinnable window) is not reproduced here; see the lists at the end.  
**Read from:** tv/capture_win.ps1:held branch, NearMiss · tv/control_app.py:_start_capture, _capture_health, _ensure_pillow_at_boot · tv/console_doctor.py:_check_this_machine_can_decode_a_frame · tv/river.py:j_disk

<a id="rec-07"></a>
### REC-07 — A receipt says SEEN for a floor read and REGISTERED for a stash read, routes to the right place, and shows its own frame

**Proves:** #56 / v2230: a floor read says '👁 seen' and a stash read says '🗄 registered', plus v1506's how-sure chips and v1616's click-through to the item. The stash chip and the click-through have not been seen again since.  
**Setup:** During REC-01's ON AIR (the receipts list is empty off-air), in a private solo game in town. Goblin Toe has been moved from the stash to the inventory (REC-01 setup), and War Traveler is in the stash. The AI READS tag reads '· live'.

**Items:**
- Goblin Toe: a low-value unique (Light Plated Boots) in your stash sightings, safe to drop in a private game if picked straight back up. Its identified floor label carries the unique name, so the only difference from the stash read is the SCENE, which is exactly what the chip must follow.
- War Traveler: a unique and therefore a grail name, so its click must land on the Uniques card rather than Tools.

**Steps:**
1. Close every panel. Drop Goblin Toe on the town floor. Walk a few steps away and back, stop with its label visible (hold Alt), and hold still for 6 s. With no inventory open, the scene word can only be a floor word. Then pick Goblin Toe back up: items left on the ground are lost when the game closes.
2. Open the stash, move onto War Traveler and hold still for 6 s.
3. In AI READS · live, find both rows and hover each one.
4. Click the War Traveler row.
5. If any row names a non-grail item (for example a magic charm, or a bare base like 'Ring'), click it.

**✅ Expect:**

Goblin Toe row: '🔴 read Goblin Toe · LOOT · …', '· TOWN · …' or '· FARMING …', with the chip '👁 seen' and never '🗄 registered'.

War Traveler row: '🔴 read War Traveler · STASH · …' with '🗄 registered'.

Each row carries 'live guess', or '✓ gated' if the accuracy gate certified it. A refused row shows '⚠ HELD'.

Hovering a row shows ITS frame: the floor, then the open stash.

Clicking War Traveler opens the Uniques chronicle on War Traveler's card. A non-grail row opens the Tools tab with the name seeded.

**❌ Fail looks like:**

- A floor row wearing '🗄 registered': the v2230 defect, a sighting claimed as banked. First check that no inventory panel was open.
- A stash row with no chip.
- Hovering shows another row's frame.
- The War Traveler click lands on Tools or does nothing, or the toast reads 'couldn't locate War Traveler'.
- A Tools landing that paints a blank body: the same symptom as the open 'Choose in inbox lands on a blank Tools page' report. Cross-reference it rather than diagnosing it again.

**🔎 Debug first:** /api/status → receipts[] (own.banked, own.why, gate.pass, refs.frameId, refs.scene). The journal row's scene word in tv/sessions.jsonl. Eagle row 'readers agree'.

**Cost:** Rides REC-01 (+3 minutes). About 2 paid reads.  
**Unknowns:** Whether the reader calls the floor scene loot, town or gameplay is UNKNOWN; all three must give 👁 seen. With EYES on PRIMARY, Grok's scene word is not checked against that vocabulary, so a stray word would show NO chip (UNKNOWN). Whether '🗄 registered' is TRUE, meaning War Traveler is actually filed in the Vault afterwards, is the vault area's scenario: the chip is inferred from the scene word, not from a store.  
**Read from:** tv/control_app.py:_receipts_stream, _diablo_scene_label · tv/vault_retro.py:OWNERSHIP_SURFACES · tv/control_ui.html:_receiptRow, _routeReceipt

<a id="rec-08"></a>
### REC-08 — The rolling prune frees only near-duplicate blank frames and keeps every tooltip frame

**Proves:** The v2986 rolling prune and its LaneCanary on real footage: it frees only near-duplicate blank frames and keeps every tooltip frame. It deletes irreversibly and has never been watched acting on your footage.  
**Setup:** REC-01's session, kept on air for at least 6-7 minutes. Minute 0-1: no panel open, standing completely still in town (the candidates to free). Minutes 1-2: the Dwarf Star and Raven Frost hovers (the frames that must be kept). The prune runs only while the agent is alive, needs at least 200 loose frames (about 3.3 minutes at 1 frame per second), and only touches frames older than 180 s.

**Items:**
- Dwarf Star and Raven Frost tooltips from REC-01: text-bearing frames the prune must never free. They are placed in minutes 1-2 so they fall inside the oldest-120 window that the passes at minutes 5-7 actually examine.

**Steps:**
1. Before On Air, note status.prune in /api/status.
2. Between minutes 4 and 7 on air, reload /api/status and read prune.passes, prune.framesDropped and prune.lastSay.
3. After End Session, open REC-01's reel in the theatre (REC-04) and scrub through the minute-1-to-2 hovers.
4. Compare index.json n + prune.framesDropped with the seconds on air.

**✅ Expect:**

prune.passes rises by one each minute on air, counted even when the pass does nothing. prune.lastSay moves from 'ARMED (v2986)…' to 'only N loose frame(s) - the floor is 200'. It then moves (possibly via 'nothing older than the 180s grace') to 'kept every frame more than 0.020 from the one before it'. When blank frames were candidates, it adds '; K blank frame(s) freed (<canary say>), M kept for want of that proof'.

Every Dwarf Star and Raven Frost tooltip frame from minutes 1-2 is still in the sealed reel. The gate calls a tooltip over the stash 'panel' or 'no', and both are always kept.

n + framesDropped ≈ seconds on air, minus warm-up.

prune.passes stops rising after End Session.

**❌ Fail looks like:**

- A tooltip moment is missing from the theatre while frames around it exist.
- framesDropped > 0 with a lastSay that does not name a canary.
- passes rising while off air.

A '🗜 rolling prune: dropped N duplicate frame(s)' line in tv/control_app.log is NOT a failure by itself: it is the expected result for the still first minute.

**🔎 Debug first:** /api/status → prune. tv/control_app.log '🗜 rolling prune'. The reel's index.json n. The per-reason keep counts (_PRUNE_KEPT) are not on status, so the lastSay sentence is the only reason shown on screen.

**Cost:** Rides REC-01 (keep it on air for at least 6-7 minutes). About 0-2 extra reads.  
**Unknowns:** The framesDropped count is UNKNOWN in advance. It depends on whether the gate reads the town screen as 'no' (text, which is kept) or 'unknown' (silent, which can be freed), and on whether the canary finds a known-good probe. 0 dropped is an honest outcome. The law under test is that nothing text-bearing goes.  
**Read from:** tv/control_app.py:_prune_once, _prune_note, _prune_loop, LaneCanary

---

## 4 · Fleet and console health

The fleet panel (#240), the own-window board claim (#239), ALT parity (#141), needs-you vs Claude-owes rows, and relaunching after a fix-only change. Baseline on 2026-09-25: your Mac console last relaunched itself at 06:48 local; every fix since then needs a manual relaunch. The ALT is 3 commits behind (REG-1300..REG-1303 not pushed at the time of writing).

<a id="relaunch-01"></a>
### RELAUNCH-01 — A fix: commit never relaunches the console. Relaunch your Mac console by hand and watch today's fixes go live

**Proves:** A fix: commit never relaunches the console (the drift loop compares version strings only), so REG-1286..REG-1303 reach your screen only through a manual relaunch. Also proves the relaunch button end to end.  
**Setup:** Your Mac with the console open, NOT on air, and no chronicle or vault sweep running (the sweep meter under THE FLEET should be idle). Do FLEET-01 steps 1-2 first if you can, because they need the old window. Close every panel with its ✕ or a backdrop click, never Esc (see the lists at the end: Esc on these panels also quits the console).

**Items:** none needed.

**Steps:**
1. Click the version label in the footer. It reads like 'Chiliad 504 · 🦅 N not measured · 🔧 N mine'. THE STATE OF THIS CONSOLE opens. For each of these five rows, note whether it is listed and under which heading: running code matches disk / this process runs the code on disk / window runs the document on disk / a present machine has a fresh last-seen / a tally agrees with its own ledger verdict. Close the panel with the ✕.
2. In any browser on the Mac, open `/api/own_board_claim` on the console (port 17772) and note the answer.
3. Go to the TV·D view and open the ⚙ ADVANCED drawer. Press '⟲ relaunch'. It changes to '⟲ sure? the window will reopen'. Press it again within 4 s.
4. Let the window close and reopen. The footer still reads Chiliad 504. That is the point: nothing in the version shows a fix-only change.
5. Reload the browser tab from step 2.
6. Wait for the second eagle pass after the reopen, about 12 min (the first pass runs at boot and the next one 10 min later). You do not need to press ↻ on THE FLEET, because by code reading it does not refresh the roster these doctor rows judge. Open THE STATE OF THIS CONSOLE again, read it, and close it with the ✕.

**✅ Expect:** BEFORE (step 1): the three code rows are under 'WAITING ON CODE — not yours to fix', each with the word CLAUDE OWES and no button. They read 'this server is the code as it was Nh ago - control_app.py was rewritten after it loaded, so PAGE changes are live and SERVER changes are not. Restart to pick them up. (organs: console_doctor.py)', 'N function(s) in this process are loaded from bytecode that DISAGREES with the source on disk - ...', and 'THE WINDOW IS RUNNING AN OLDER DOCUMENT THAN THE TREE — it was handed <12-hex id> and this server would now serve <a different 12-hex id> ...'. The ids change with every edit, so compare them only with each other. VERSIONS shows console v3504 with the verdict 'in sync', and there is no RELAUNCH NOW strip. BEFORE (step 2): {"ok": false, "msg": "not found"}. STEP 3: if a paid read or a sweep is in flight, a toast ends '... IT IS HELD and will fire by itself when the work finishes; you do not need to press again.' That is correct, not a fail. AFTER (step 5): {"ok": true, "may": false, "snapshots": <your ledger-backup count, more than 0>, "tally": ["sets 134", "uniques 309", "runewords 99"], "why": "this machine held a populated board before (<n> ledger backup(s), newest ledger_....json; banked tally sets 134, uniques 309, runewords 99) - it is RESTORED, never replaced by a new empty world. Restore from the newest ledger backup, or press 'This browser is mine' if a new world is really what you want."}. The tally figures are your banked tally at that minute (134/309/99 at 13:22Z). AFTER (step 6): none of the three code rows is listed. 'a present machine has a fresh last-seen' is not listed, or it sits under NOT MEASURED reading 'this console holds no fleet roster yet' (first pass only). If it is ever listed as MISSING, its sentence must end '(aged at the roster's own clock; this roster is Nm old)'. 'a tally agrees with its own ledger verdict' is either not listed, or listed under WAITING ON CODE as CLAUDE OWES, naming only Konyo: 'Konyo <ledger> is SYNCED but its old seal says never synced (measured=False, no measuredBy) - current cards read the provenance and show <n>, an older card still hides it; restarting that console onto the per-ledger seal clears it'. That is this Mac's pre-relaunch beacon, still in the roster the doctor judges. By code reading, that roster refreshes only on the hourly eagle pass, so the row may stay listed for up to about an hour. The three code rows stop counting toward '🔧 N mine'.

**❌ Fail looks like:** The window never reopens: the console is dead, so reopen it the usual way. Step 5 still answers 'not found'. Any of the three code rows is still listed at the second pass. 'a present machine has a fresh last-seen' is listed as MISSING with '... Konyo (NNm)' and no '(aged at ...)' clause, which means the pre-REG-1302 doctor is still running. 'a tally agrees ...' still names Konyo more than ~70 min after the relaunch while the Mac is online, or uses the pre-REG-1301 words '... figure is hidden as never synced' about Konyo.

**🔎 Debug first:** tv/.console_boot.log: it must gain a 'relaunch-exec {"where": "/api/relaunch"}' line, then a 'boot' line with the same pid whose parentWait says 'same pid (POSIX execv replaced the image in place)'. Then tv/.relaunch_receipt.json: where=/api/relaunch. Its toVersion is ALWAYS null, because _before_exec calls write_receipt(where) with no version, so that is not the fault. Then the tail of tv/control_app.log for a boot traceback. Then GET /api/status: moduleFreshness (stale:false, loadedAtMs after the press), uiBeat.docVer and eagle.rows.

**Cost:** About 2 min hands-on plus about 12 min waiting. No paid reads.  
**Unknowns:** The exact '🔧 mine' figure afterwards is UNKNOWN, because other rows move on their own. Whether this relaunch can drop the Mac's Screen Recording grant is UNKNOWN. The route records screenRecordingBefore; if capture reads dead afterwards, put the console back with your usual launcher (tv/tvd-scan.sh, never --force). The claim that the doctor's fleet rows judge a different roster from the panel's is by code reading, not measured (see the lists at the end). If a new commit lands on main after the relaunch, the code rows come back, and that is correct, not a fail. Two rows disagree about the page: 'running code matches disk' says 'PAGE changes are live' while 'window runs the document on disk' says the window holds an older page. Both are true: a reload serves the new page, and the window has not reloaded.  
**Read from:** tv/control_app.py:_drift_once, _drift_loop, _module_freshness_now, /api/relaunch, own_board_may_autoclaim, _before_exec · tv/console_doctor.py:running-code rows, last-seen row, tally-verdict row · tv/win_relaunch.py:write_receipt

> **Note:** Run this early. Until your Mac console relaunches, everything you look at runs old code. Do FLEET-01 steps 1-2 first, because they need the old window.

<a id="fleet-01"></a>
### FLEET-01 — Each console shows its own counts on YOUR Mac and your ALT (#240), before and after the relaunch

**Proves:** #240 (REG-1289 per-ledger seal, REG-1296 old-peer fallback) on your screen and the ALT's: a never-synced ledger blanks only its own cell, and your own row never reads 'never synced'. So far confirmed only on GrokBot's screen.  
**Setup:** Do steps 1-2 BEFORE RELAUNCH-01 and step 3 after it. The BEFORE half holds only while 'window runs the document on disk' is still listed; if it is not, your window already has today's card and step 1 shows the AFTER state. The ALT console must be open and online. Sessions view, right rail, 🖥 THE FLEET. Hover only. If a click opens the 'yours vs theirs' window, close it with ✕, not Esc.

**Items:**
- No game item. The discriminating ledger is the ALT's RUNEWORDS. It is UNSYNCED on that board while its sets and uniques are SYNCED, so exactly one cell of its row must read '—'.

**Steps:**
1. Mac, before the relaunch: hover the row 'Konyo' (the word beside it reads 'this console') and read the card's counts line.
2. Hover 'Konyo ALT TEST' and read its counts line and the small provenance rows above it.
3. Do RELAUNCH-01. Then hover 'Konyo', 'Konyo ALT TEST', the GrokBot row in the ONLINE group, 'Dean' (offline) and 'Wife PC'. Hover the '—' cell itself for its reason.
4. On the ALT: open its console → THE FLEET, press ↻, then hover its own row and the 'Konyo' row.
5. At the same minute, check the Mac's and the ALT's own board headlines (Sets / Uniques / Runewords) against their rows.

**✅ Expect:** BEFORE (Mac, old card): your own row reads 'SETS — · UNIQUES — · RUNEWORDS —'. That is the #240 defect, reproduced on your screen. The ALT row reads 'SETS 2 / 135 · UNIQUES 4 / 403 · RUNEWORDS 0 / 99': a never-synced zero shown as a count. AFTER (Mac; the figures are today's and move as each machine plays). Konyo: word 'this console', provenance rows 'uniques SYNCED · sets SYNCED · runewords SYNCED', counts 'SETS 134 / 135 · UNIQUES 309 / 403 · RUNEWORDS 99 / 99'. Konyo ALT TEST: provenance 'uniques SYNCED · sets SYNCED · runewords UNSYNCED', counts 'SETS 2 / 135 · UNIQUES 4 / 403 · RUNEWORDS —'. The '—' cell's hover reads 'differs — this machine reports 0, this console has 99 — a difference of 99. not every ledger here is a count: runewords was never synced on that board, so a 0 there means nothing was ever handed over, not that nothing was found'. GrokBot (online, v3504): 'SETS 129 / 135 · UNIQUES 309 / 403 · RUNEWORDS 99 / 99'. Two machines share the name GrokBot, so both rows show the name with a machine suffix. The OFFLINE one (v3377, 'SETS 128 / 135 · UNIQUES 309 / 403 · RUNEWORDS 99 / 99') is a stale second install and not part of this test. Dean (offline, v3404, no provenance rows, a build older than the seal): 'SETS 132 / 135 · UNIQUES 0 / 403 · RUNEWORDS 98 / 99'. Its 0 is shown as a count by design for a peer too old to send a verdict. Wife PC: word 'no report', body 'nothing recorded'. ON THE ALT: its own row is 'this console' with 'SETS 2 / 135 · UNIQUES 4 / 403 · RUNEWORDS —'. The Konyo row shows 134 / 309 / 99 and never '—', even before the Mac relaunches, because the ALT's card reads the Mac's provenance (REG-1296) once its window has today's page. The Mac's and the ALT's rows must equal each machine's own board headline at the same minute, except your Mac's uniques (see unknowns).

**❌ Fail looks like:** Any of these fails: a row whose provenance rows all say SYNCED but whose three cells are all '—' (after the relaunch); the ALT's runewords reading '0 / 99' after the relaunch; your own row still reading '—' after the relaunch; the Mac and the ALT carrying the same triple (your 'same person on all three' report).

**🔎 Debug first:** GET /api/fleet in a browser → that row's tally.measuredBy, tally.measured and tally.ledgerVerdict.ledgers[].provenance. Then the doctor row 'a tally agrees with its own ledger verdict'. If the card still looks old, check the doctor row 'window runs the document on disk' (on the ALT as well).

**Cost:** 5 min. No paid reads.  
**Unknowns:** On the Mac, the word beside 'Konyo ALT TEST' reads 'differs' with the hover '3 of 3 ledger(s) disagree with this console'. That count includes the never-synced runewords 0 against your 99, because _machineWord ignores measuredBy. Whether a never-synced ledger should count as a disagreement has not been ruled, so note it but do not fail #240 on it. Your own uniques read 309 on this card (the banked tally) and 312 in the cross-reference footer (FLEET-02) at the same minute. Which one your board headline shows is UNKNOWN; record it, and do not fail #240 on that ledger. Every number moves as the machines play, so compare relations, not today's literals.  
**Read from:** tv/control_ui.html:_bar, _measOf, _machineWord, _fleetName · tv/control_app.py:_fleet_overlay_local_tally, /api/fleet

> **Note:** Steps 1-2 must happen BEFORE RELAUNCH-01.

<a id="claim-01"></a>
### CLAIM-01 — Restore, never reseed: a machine that held a board is never auto-claimed into a fresh world (#239)

**Proves:** #239 / REG-1291 on real machines: a machine that once held a board is RESTORED, never auto-claimed into a fresh world, and only the console's own window may auto-claim.  
**Setup:** The ALT console must be running code that includes the #239 fix (it is on origin). Its doctor must NOT list 'running code matches disk'; if it does, do ALT-01's relaunch first. The Mac must be after RELAUNCH-01. Close THE STATE OF THIS CONSOLE with its ✕, never Esc.

**Items:**
- Bane Ash (unique short staff), Gull (unique dagger), Lenymo (unique sash): three of the ALT's own 4 uniques. Your Mac does not hold them (GET /api/fleet_compare, 13:22Z) and they are not in the owner's _GRAIL_SEED, so they must still be ticked on the ALT afterwards (restored, not replaced).
- The Stone of Jordan (unique ring) and Annihilus (unique small charm): both are in the owner's _GRAIL_SEED and your Mac holds both, while the ALT holds neither. If either shows as found on the ALT, the owner's seed was laid over its world (the v2692 contamination).

**Steps:**
1. ALT: open `/api/own_board_claim` on the console (port 17772) in Edge and read it.
2. ALT: THE STATE OF THIS CONSOLE → look for 'board is claimed'.
3. ALT (optional, 2 min; skip it if you are unsure): open an Edge InPrivate window at `/board` on the console (port 17772). Wait 15 s. Do NOT press the button. Close the InPrivate window.
4. ALT board: check the Sets and Uniques headlines and the ticks on Bane Ash, Gull and Lenymo, then on The Stone of Jordan and Annihilus.
5. Mac: open the same URL as step 1.

**✅ Expect:**

1. {"ok": true, "may": false, "snapshots": <n>, "tally": ["sets 2", "uniques 4"], "why": "this machine held a populated board before (... banked tally sets 2, uniques 4) - it is RESTORED, never replaced by a new empty world. Restore from the newest ledger backup, or press 'This browser is mine' if a new world is really what you want."}. Runewords is absent from the list because its have is 0. If the ALT has ledger backups, the parenthesis starts '<n> ledger backup(s), newest ledger_....json; '. 2. One of three things.

- (a) The row is not listed: OK, the board is claimed and there was nothing to decide.
- (b) It is listed under WAITING ON CODE as CLAUDE OWES (it asks nothing): 'the board is an UNCLAIMED guest world (prefix ...) holding N ledger entries — ... The console's own window did NOT claim it by itself: this machine held a populated board before (...)'.
- (c) It is under NOT MEASURED as CAN'T ASK: 'the board is not open in the window — ... Open the board to find out.' In case (c), open the board in the console window and look again. 3. The bar 'This browser has its own empty world.' with '✋ This browser is mine' stays for the whole 15 s. It never turns into 'this console’s own board — claiming…' and the page never reloads itself. 4. The ALT reads Sets 2 / 135 and Uniques 4 / 403, with Bane Ash, Gull and Lenymo ticked and The Stone of Jordan and Annihilus not ticked. 5. Mac: may:false, with tally equal to your banked tally (sets 134, uniques 309, runewords 99 at 13:22Z) and snapshots more than 0.

**❌ Fail looks like:** Any of these fails: may:true on either machine; 'not found' after a relaunch; the InPrivate page reloading itself or its button changing text; the ALT's uniques jumping toward your Mac's ~309, or The Stone of Jordan or Annihilus appearing there; 'board is claimed' under WAITING ON CODE without the sentence about the refusal.

**🔎 Debug first:** The two records own_board_may_autoclaim reads on that machine: the banked tally (tv/board_tally.json) and the d2r_ledger_backups folder in that user's home. Then the doctor row 'board is claimed'. Afterwards, the ALT's /api/fleet row, to confirm SETS 2 / UNIQUES 4 did not move.

**Cost:** 5 min. No paid reads.  
**Unknowns:** Whether the ALT's board is already claimed is UNKNOWN from here. If it is, step 2 is simply 'not listed' and the auto-claim never had to decide; the GET in step 1 is then the only proof of the refusal. The InPrivate tab is a guest board served by the ALT's own console. An all-zero first post is refused at the door, but a guest world that re-seeds the owner's finds would post non-zero counts and be banked. Step 4 exists to catch that. If the ALT's row moves, stop and report. The may:true path cannot be staged by hand (see the lists at the end).  
**Read from:** tv/control_app.py:own_board_may_autoclaim, board_tally_merge · bible.html:_d2rClaimThisBrowser, _GRAIL_SEED · tv/console_doctor.py:_check_the_board_world_is_claimed

<a id="fleet-02"></a>
### FLEET-02 — The cross-reference names the items only the ALT holds (Bane Ash, Gull, Lenymo) and the one set piece neither machine holds

**Proves:** #240's 'as if im the same person on all three', item by item: the cross-reference names the items only the ALT holds and the one set piece neither machine holds.  
**Setup:** Both consoles running and the ALT online in THE FLEET. Close the window with ✕ or a backdrop click, never Esc (see the lists at the end).

**Items:**
- Bane Ash, Gull, Lenymo (uniques): on the ALT's board and NOT on your Mac's. They can appear under 'they have · you do not' only if the panel really reads the ALT's own list.
- Cow King's Hooves (heavy boots, a piece of the Cow King's Leathers set): the one set piece neither machine holds, and the only name 'you both need' may show for Sets.
- The Stone of Jordan, Annihilus (owner-seed uniques): your Mac holds both, so on the Mac they belong in 'you have · they do not'. On the ALT's own view they must appear only under 'they have · you do not', never among the ALT's own holdings.

**Steps:**
1. Mac: Sessions → THE FLEET → click the row 'Konyo ALT TEST'. The 'yours vs theirs' window opens on SETS.
2. Read the three columns and the footer.
3. Click the UNIQUES tab inside that window, then read the columns and the footer.
4. Close it with the ✕.
5. ALT: click the 'Konyo' row and repeat SETS and UNIQUES from its side. Close with ✕.
6. ALT board: open Uniques and find Bane Ash, Gull and Lenymo.

**✅ Expect:** Mac, SETS: 'they have · you do not' shows 0 and reads 'nothing they hold is new to you'. 'you have · they do not' shows 132 tiles. 'you both need' is Cow King's Hooves (heavy boots) alone. The footer starts '134 / 135 yours · 2 / 135 theirs · 2 shared'. Mac, UNIQUES: 'they have · you do not' is exactly Bane Ash, Gull, Lenymo. 'you have · they do not' is the rest of your list (311 today). 'you both need' shows an em-dash in its count and the reason (the roster names 398 against 403 posted, so a both-need list cannot claim to be complete), NOT '0'. The footer starts '312 / 403 yours · 4 / 403 theirs · 1 shared'. The ALT's side is the mirror image. UNIQUES 'you have · they do not' is Bane Ash, Gull, Lenymo, and 'they have · you do not' is your Mac's 311 (including The Stone of Jordan and Annihilus). SETS 'they have · you do not' is 132, 'you have · they do not' is empty ('nothing you hold is new to them'), and 'you both need' is Cow King's Hooves. On the ALT's board, Bane Ash, Gull and Lenymo are ticked, and The Stone of Jordan and Annihilus are not.

**❌ Fail looks like:** Any of these fails: 'they have · you do not' is empty on UNIQUES, or lists names your Mac already has; the ALT's side lists your ~309 as its own; the uniques 'you both need' reads 0; 'the answer arrived and this panel could not draw it'; a one-sided panel reading 'not published — ...'.

**🔎 Debug first:** GET /api/fleet_compare?machine=<the row's data-fleet-machine>&ledger=uniques → theyHaveIDont / iHaveTheyDont / neitherHas / neitherWhy / mineN / theirsN. Then /api/fleet → that row's masks and maskWhy.

**Cost:** 5 min. No paid reads.  
**Unknowns:** Your own uniques read 309 on the fleet card and 312 (mineN) in this window's footer at the same minute: two numbers for one quantity (the banked tally against the board's live mask). If they still differ on screen, record both; which one is right is UNKNOWN. On the ALT, whether 'you both need' for UNIQUES is also an em-dash depends on the total the ALT's own board posts, which is UNKNOWN from here. The names of the ALT's two set pieces and of its 4th unique (the one shared with the Mac) are not in the compare output, so read them off the ALT's own board.  
**Read from:** tv/control_ui.html:_fleetCompare · tv/control_app.py:fleet_compare · tv/fleet_mask.py

<a id="alt-01"></a>
### ALT-01 — ALT parity after a pull (#141): a fix-only pull, a manual relaunch, and 'handoff lanes drained' is no longer billed

**Proves:** #141 / REG-1290 on the ALT's own screen (the handoff lanes read UNMEASURED and are not billed), the Windows relaunch by button (#225), and that a fix-only pull lands on disk but not in the running process.  
**Setup:** Do this after the next push lands. At the time of writing, local main is 3 commits ahead of origin (REG-1300..REG-1303 are not on the ALT yet). The ALT console must be running and idle. Close THE STATE OF THIS CONSOLE with its ✕, never Esc.

**Items:** none needed.

**Steps:**
1. Wait at least 5 min after the push (the ALT auto-pulls every 300 s). On the ALT, read the footer label, then open THE STATE OF THIS CONSOLE and read VERSIONS and WAITING ON CODE. Close it with ✕.
2. TV·D → ⚙ ADVANCED → ⟲ relaunch, pressed twice (arm, then confirm within 4 s).
3. The window closes and reopens as a new process.
4. Once the first pass has run (the lead line stops reading not measured), read WAITING ON YOU, WAITING ON CODE and NOT MEASURED. Read them again about 12 min later.
5. On the Mac, THE FLEET: the ALT row comes back online. Hover its word.

**✅ Expect:** BEFORE (only when the push kept v3504): the footer is unchanged (Chiliad 504), there is no RELAUNCH NOW strip, and the VERSIONS verdict reads 'in sync'. WAITING ON CODE lists 'running code matches disk' (CLAUDE OWES): the console admitting it pulled code it is not running. If the push carried a new version, the ALT relaunches itself (the drift loop's execv) and there is no BEFORE state, so skip to AFTER. RELAUNCH: the window reopens within seconds. The ALT's tv/.console_boot.log gains a 'relaunch-exec {"where": "/api/relaunch"}' line, then a 'boot' line with a NEW pid whose parentWait reads waited:true ('parent exited' or 'parent already gone'), NOT 'same pid (POSIX ...)'. AFTER, first pass: the lead line reads 'nothing is waiting on you'. The one allowed exception is 'this console starts at sign-in' (DOCTOR-01), which makes it '1 thing(s) are waiting on YOU'. 'handoff lanes drained' sits under 'NOT MEASURED — unknown, which is not "fine"' with the word NEVER and 'this machine has never drained either lane (no #230 watermark, no #231 look filed), so it is not where the lanes are worked; whether the machine that works them keeps up is not measurable from here'. On later passes (it is asked hourly) the same row reads NOT THIS TICK with 'not asked this tick (PERIODIC — every 6 eagle ticks; ...) · last asked Nm ago, last state unmeasured'. It is never under WAITING ON YOU or WAITING ON CODE. 'running code matches disk', 'this process runs the code on disk' and 'window runs the document on disk' are not listed. 'this console tree is established' is not listed. On the Mac, the ALT row is online again, still SETS 2 / UNIQUES 4, and its word's hover includes 'idle · v3504 · own tree established · 0 reels on its shelf'.

**❌ Fail looks like:** Any of these fails: the window never comes back (the #225 death; the last line of .console_boot.log names the early exit, so reopen from the TV DIABLO shortcut); 'handoff lanes drained' under WAITING ON YOU or WAITING ON CODE reading '#231 has N look(s) NOT yet in the ledger; #230 has NO watermark at all'; the first pass stuck on one check for more than 15 min.

**🔎 Debug first:** The ALT's tv/.console_boot.log and tv/.relaunch_receipt.json. Then /api/status → eagle.measuring, which names the check a slow first pass sits in (REG-1248/REG-1268), and moduleFreshness. Then the row 'handoff lanes drained'.

**Cost:** About 20 min elapsed, 3 min hands-on. No paid reads.  
**Unknowns:** The #141 card's 'reads 0 missing' does not say which count. PASS here means nothing waiting on you from the ALT's own health, and the handoff lanes not billed. Rows under WAITING ON CODE about OTHER machines are not the ALT's parity and are not a fail. Examples: 'a tally agrees ...' naming the Mac's old seal until the Mac relaunches, or the pre-REG-1302 last-seen row if REG-1302 is not in the push. The ALT's first pass has taken minutes before (229 s + 143 s standalone), so wait for it.  
**Read from:** tv/control_app.py:_pull_once, _drift_once, /api/relaunch · tv/win_relaunch.py:wait_for_parent · tv/console_doctor.py:handoff check · tv/control_ui.html:_vxHealthRow

<a id="doctor-02"></a>
### DOCTOR-02 — A present machine is not called away just because the roster the doctor holds is old (REG-1302)

**Proves:** REG-1302: each online machine is aged at the roster's own clock, so an old roster no longer calls a present machine away. Fixture-proven only.  
**Setup:** Your Mac, straight after RELAUNCH-01. REG-1302 is committed on your tree but not pushed, so the ALT cannot run it yet. At least one other machine must stay online for the whole hour. Note the minute of the relaunch. You can use the console normally meanwhile: by code reading, focusing it or pressing ↻ does not refresh the roster this row judges.

**Items:** none needed.

**Steps:**
1. Starting about 40 min after the relaunch, open `/api/status` on the console (port 17772) in a browser every ~5 min. Find 'a present machine has a fresh last-seen' in eagle.rows and note its state and the 'this roster is Nm old' figure.
2. Stop once you have seen a pass where N is over 40, or once 70 min have passed.
3. Open THE STATE OF THIS CONSOLE and close it with ✕.

**✅ Expect:** The row's state is 'ok', with why 'all N online machine(s) carry a last-seen inside the 40m window their presence implies (aged at the roster's own clock; this roster is Nm old)'. A roster older than 40 min with the row still 'ok' is the whole proof. By code reading, the roster this row judges is refreshed only on the periodic eagle pass (the 1st pass and every 6th), after the row has run. So the stated age climbs by about 10 min per pass and should read roughly 45-55m on the pass that ends around 50-58 min after the relaunch, then drop back. In step 3 the row is not listed.

**❌ Fail looks like:** State 'missing' with 'N of N online machine(s) carry a last-seen older than the 40m presence window ...: Konyo (5Xm) ...' and no '(aged at ...)' clause, which is the pre-REG-1302 behaviour. Or UNKNOWN 'the cached roster carries no clock'. If the stated age never goes above 40, the test did not exercise the defect: that is inconclusive, not a pass.

**🔎 Debug first:** The row's why in /api/status, which states the roster age. Compare it with /api/fleet's 'now' and each online row's 't'. By code reading, the doctor imports control_app as a second module (the console runs it as __main__), so the roster in _FLEET_PRESENCE_CACHE that this row reads is not the one /api/fleet serves the panel. It is filled only when 'engines corroborate' runs corroborate._fleet() on a periodic pass.

**Cost:** About 5 min hands-on spread over roughly an hour, which can overlap a play session. No paid reads.  
**Unknowns:** The two-roster mechanism comes from code reading and has not been measured. It explains the 55-59 min ages REG-1302 recorded, but if something else refreshes the doctor's roster, the age may never pass 40 and the test is inconclusive. If the other machines go offline during the hour, the row turns 'ok' or UNMEASURED trivially, so note which machines were online. On the first pass after boot this row is expected to read UNMEASURED ('this console holds no fleet roster yet'), because nothing has filled the doctor's roster yet.  
**Read from:** tv/console_doctor.py:_check_a_present_machine_has_a_fresh_last_seen · tv/control_app.py:fleet_presence, _FLEET_PRESENCE_CACHE · tv/corroborate.py:_fleet

<a id="doctor-01"></a>
### DOCTOR-01 — What a row that needs YOU looks like next to one Claude owes (the ALT's sign-in question)

**Proves:** The #223 / #226 split on real screens: a row that asks you something is amber with CHOOSE IN INBOX, and a row that asks nothing is CLAUDE OWES with no button. Also REG-1263 / REG-1282 and the #25 landing.  
**Setup:** The ALT console, after ALT-01. On your Mac this row is UNMEASURED by design ('only a Windows console needs a sign-in start - this machine starts through its own launcher'). Close THE STATE OF THIS CONSOLE with its ✕, never Esc.

**Items:** none needed.

**Steps:**
1. ALT: THE STATE OF THIS CONSOLE → find 'this console starts at sign-in', and pick any WAITING ON CODE row for contrast.
2. If the sign-in row is under WAITING ON YOU, press 'YOUR CALL — CHOOSE IN INBOX →'.
3. On the question card, press 'Ask me next week'. That is the reversible answer. 'Yes, set it up' hands Claude a standing change on your PC, so press it only if you want that.
4. Open THE STATE OF THIS CONSOLE again.
5. If the row was never under WAITING ON YOU: open the Startup folder (Win+R, shell:startup) and Task Scheduler, read-only.

**✅ Expect:**

As a needs-you row: amber, under WAITING ON YOU, with the button 'YOUR CALL — CHOOSE IN INBOX →' and the note 'Start TV DIABLO on this PC when you sign in? · nothing starts this console when the PC signs in: no 'TV DIABLO at sign-in' task and nothing in the Startup folder - after a reboot it stays off until someone opens it · your choices: Yes, set it up · No, I open it myself · Ask me next week'. The lead line reads '1 thing(s) are waiting on YOU', and the footer label carries '🦅 1 needs you'. For contrast, a WAITING ON CODE row carries the word CLAUDE OWES, with no button and no amber. CHOOSE IN INBOX closes the panel, opens the board on Tools, and puts the question in view. If the question cannot be reached, a toast says 'couldn’t open that question in the inbox — …' or 'couldn’t open that question — the board pane isn’t ready'. It must never leave a blank Tools page. After 'Ask me next week', the row sits under 'ANSWERED BY YOU — held until it lapses or the question changes' as 'you: Ask me next week · change →' with 'asked again after <a date a week out>, or sooner if the question changes', and 'needs you' is gone from the footer. If the row was never needs-you, it must be one of three things.

- (a) Under ANSWERED BY YOU: it was answered earlier.
- (b) Not listed (OK): a Startup shortcut whose bytes name start_tvd_win or control_app.py, or a task named 'TV DIABLO at sign-in', exists.
- (c) Under NOT MEASURED as CAN'T ASK: schtasks could not be asked, or a Startup entry could not be read. A Startup entry that is only the game's own Diablo shortcut must NOT make it OK.

**❌ Fail looks like:** Any of these fails: an amber WAITING ON YOU row with no CHOOSE IN INBOX button; a WAITING ON CODE row with a button; '⚠ the counter and this panel disagree (...)' in the lead; CHOOSE IN INBOX landing on a blank or black Tools page (#25); the row reading OK while Startup holds only a game shortcut.

**🔎 Debug first:** /api/status → eagle.needsYouWhat, mineWhat and answeredWhat, plus the row's asks / openAsks / answered. Then your answers store (his_answers.json through _decision_path, git-ignored). For a bad landing, the board's d2rOpenAsk result (#25).

**Cost:** 5 min. No paid reads. Answering writes your own answers store; that is your ruling and it is reversible with 'change →'.  
**Unknowns:** Which of the four states the ALT is in today is UNKNOWN. REG-1263 measured zero Startup entries on 09-20, while REG-1290 counted only one missing row on 09-25, so the question was not open then. Your Mac has no row in this area that can ask you anything: 'no machine went quiet mid-restart' asks only when a peer dies mid-restart.  
**Read from:** tv/console_doctor.py:_sign_in_start, _launches_this_console, _ask_sign_in_start · tv/control_app.py:eagle_partition · tv/control_ui.html:_vxAskRow, _hubGoAsk

<a id="esc-02"></a>
### ESC-02 — The designed Esc ladder in the chronicle inbox: the question answers 'no', then the inbox closes, and the console stays up

**Proves:** REG-1254 on the ALT's WebView2: the same Esc ladder as ESC-01, on a machine where a wrong key cannot touch your real chronicle.  
**Setup:** The ALT, idle (off air, no sweep), on the TV·D view (the 📜 Inbox pill lives in the rail's signal panel, which Sessions hides), with the pill showing a plain N ≥ 1. Do NOT use your Mac: an accidental 'Promote all' there writes your real chronicle, and there is no unfind. While the question is up, press ONLY Esc. Focus sits on 'Not now', but Tab and Enter could reach 'Promote all N'. Press Esc exactly TWICE in total. A third Esc lands on the empty console and quits it by design (see the lists at the end).

**Items:**
- Any pending chronicle-inbox proposal. The question counts them, so no specific item is needed. Whether the ALT's inbox holds any today is UNKNOWN; if the pill shows '0' or '0/N' (nothing pending), skip this scenario.

**Steps:**
1. ALT: press 📜 Inbox N, then 'Accept ALL pending…'. The question 'Promote ALL N inbox items to FOUND (chronicle write)?' appears with 'Not now' and 'Promote all N'.
2. Press Esc once. Check that the question is gone and the inbox is still open with the same N.
3. Press Esc once more, then stop pressing keys.
4. Confirm the console is alive on the TV·D view and the pill still shows the same N.

**✅ Expect:** After Esc 1: the question is gone, the inbox is still open, and the inbox count is unchanged (nothing promoted). After Esc 2: the inbox is closed and the console is alive on its TV·D view with the same pill count. There is no 'Leaving console…' toast at any point.

**❌ Fail looks like:** Esc 1 closes the INBOX and leaves the question on screen with its yes button armed (the REG-1254 bug). Or a 'Leaving console…' toast appears after either Esc and the window closes: reopen it from the TV DIABLO shortcut and report. Or the inbox count changes at any point, which means a promotion happened: stop and report.

**🔎 Debug first:** The keydown listeners in order: the inbox's capture listener (answers the question 'no', or closes the inbox, and stops the event in both cases), then the question's own listener, then the empty-console handler. On a Mac, tv/control_app.log records a quit's author. On the ALT it does not (pythonw drops stdout); tv/.console_boot.log shows only the next boot.

**Cost:** 3 min. No paid reads. Risk: a wrong key promotes the ALT's inbox, which is why this runs on the ALT only.  
**Unknowns:** Whether the ALT has any pending inbox items is UNKNOWN. It is assumed, not measured, that WebView2 on the ALT delivers Esc to the console document while the inbox modal has focus. REG-1254's real-Chrome repro used the same path.  
**Read from:** tv/control_ui.html:chAsk, chAcceptAllConfirm, inbox capture Esc listener, empty-console quit · tv/control_app.py:/api/quit · tv/test_escape_answers_the_question_no.py

> **Note:** Same ladder as ESC-01 (Chronicle), which runs on your Mac's WebKit window instead. See ESC-01's note.

---

## Cannot be tested by hand yet

| Area | What | Why not | What unblocks it |
|---|---|---|---|
| Vault | REG-1280: a shared-stash item survives the vault cleanse | No Vault surface shows shared-stash ownership. Sunder charms are never given a locker, ownedPool drops them, and the tally does not move. | A surface that renders shared-stash ownership, which first needs your ruling on what "shared stash" means on screen (finding 1). Until then it is guarded by a node test only. |
| Vault | #60 per-item facts on a panel | No panel prints sockets, eth, quality or variants. The doctor row can turn OK from a unique's quality alone. | A ledger row that renders the facts (vault_retro keeps `variants` off the board until then). Today: raw GET `/api/vault_ledger` (VAULT-ATTR-01). |
| Vault / Chronicle | #53 magic/rare tag on a panel | `vocab` appears in no panel. It shows only in the doctor row *item vocabulary* and in GET `/api/vault_sweep`. | A renderer for `vocab`, and keeping the tag on owned rows (finding 10). |
| Vault | #174 v-C `.d2s` import: EXACT stats and the class / level / skills / mercenary panels | `tv/d2s_read.py` has no caller, and *⇪ Import .d2s* is disabled by design. | Wiring v-C. You can check one thing today: the eagle row *save reader tables* should read ✓ on your Mac. |
| Vault | #174 v-B (MULE-VB-01, MULE-VB-02) | It exists only in its unmerged worktree. | Merge v-B, then relaunch. |
| Vault | #174 v-D skill trees and v-E auto-route ("a manual placement always wins") | Not built. Today it can be proven only through the pure function `_mpEqPlace`. | Build v-D and v-E. |
| Vault | A possible REG-1280 sibling: the v677 cleanse deletes owned grail-seed names that have no mule filing | You cannot observe it by hand. | Your ruling on whether it is intended cleanup or a live deleter, then a guard. |
| Chronicle | A hand tick banks a `hand` witness (HAND-01's second half) | No UI sends `want:true`, and `/api/evidence` cannot show the tag anyway (findings 11 and 12). | Fix both findings. HAND-01's witness half then becomes a real test. |
| Chronicle | Seeing a monotonic drop | The stored peak is 3 weeks stale and is checked only in gates (finding 13). | A peak that raises itself, and a surface that shows a drop. |
| Chronicle | Refreshing the Remaining page by filming it | No code writes a filmed page into `tv/remaining/`. | A Remaining-page reader. Until then REMAIN-01 shows the dead end. |
| Chronicle | Un-tick protection at every door | It needs a standing un-tick, and creating one just to test is refused: it deletes the find date and sightings, with no redo. | A natural un-tick in the band (UNTICK-01), or fixture laws for the three doors that do not check (finding 15). |
| TV·D | REG-1300's failure branch: a worker that stops draining stdin | It cannot be produced by hand, and the eagle row only greps source. | It stays fixture-only. A live deadline instrument would make it watchable. |
| TV·D | Grok-primary live reads (👁 EYES on PRIMARY) | No scenario is written for it, and Grok's health is UNKNOWN (last error: a 140 s timeout). | Grok answering, plus a PRIMARY variant of REC-01 and REC-03. |
| TV·D | The shadow door, the text eye, and v3312's "a SHADOW reel is already rolling" | Both are OFF by your choice. | You switch them on. |
| TV·D | REG-1277's rows-not-banked half (reel …57378, 102 seal rows) | It is still inside the newest-8 shield. | Four new sealed reels, which the testing phase will produce by itself. Then read its `/api/reel_story` row. |
| TV·D | The ON AIR / MINI refusal below the 8 GB floor, and the DISK FULL banner | It needs less than 8 GB free (14.0 GB today). | Nothing, by design: fixture-only. |
| TV·D | Consoles with TV_CAPTURE=off (REG-1252, REG-1272, REG-1285) | None of your real consoles runs with capture off. | Nothing: scratch and CI consoles only. |
| TV·D | The Windows full-virtual fallback (finding 22) | It needs exclusive fullscreen on Windows. Whether your setup can do that is UNKNOWN. | A Windows machine that runs D2R in exclusive fullscreen. |
| Fleet | Esc on the state panel, the fleet window, the heart panel or the receipts view | The shipped code also quits the console (finding 23). | The fix first: add those panels to the empty-console overlay list, or stop the event. A node harness can prove it. Then the hand test is: panel open → Esc once → the panel closes and the console stays. |
| Fleet | The by-design quit on an empty console page | It is never a hand step. | Fixture-only. |
| Fleet | #239's `may:true` path (a machine that never held a board claims itself) | Staging it means emptying a store, which restore-never-reseed forbids. | A fresh install, or the Wife PC if it ever updates. |
| Fleet | A spoofed `pywebviewready` being refused | Only devtools or a harness can send one. | A harness. |
| Fleet | The "no machine went quiet mid-restart" question | It needs a peer to die between a pull and its relaunch. | Not a hand test. |
| Fleet | The auto-relaunch across a version bump | fix: commits keep the version string, so nothing relaunches. | The next vNNNN ship. |
| Fleet | REG-1300..REG-1303 on the ALT | They were not pushed at the time of writing. | The push, then ALT-01. |

### Run these when the situation comes up

- **HAND-01, NEW-01:** a genuinely new unique or set piece (94 uniques and 1 set piece were missing on 2026-09-25).
- **UNTICK-01:** only if F-Uniques shows the *❓ N marked NOT found, by you* band. It may be empty.
- **ESC-01, ESC-02:** only if the 📜 Inbox pill's tooltip starts *Chronicle · N pending* with N ≥ 1.
- **MULE-02:** only if a locker plate shows the *×N🧍* badge with N ≥ 2.
- **MULE-VB-01, MULE-VB-02:** after v-B merges.
- **ALT-01, then DOCTOR-01:** after the next push reaches the ALT.
- **REC-06:** at a Windows machine with D2R installed.

### Findings raised while checking (need a ruling or a fix, not a hand test)

1. **"Shared stash" means two different sets on screen.** The population line counts sunders, runes and shards. The SHARED STASH locker shows high-value keepers. Neither shows the sunders you registered. Needs your ruling.
2. **"N witnesses" counts sighting frames, not looks.** War Traveler reads *4 witnesses* and Horadric Cube *20 witnesses* with ONE look each. The proof chip's 2-witness bar counts frames too. The doctor row *item facts captured* says "sighting(s)" but counts names.
3. **`vault_seen.json` never drops a row that has since grounded.** 9 of the 44 "seen once" rows are already grounded, so a sweep panel can list one name as both OWNED and UNSURE. The save function's docstring says otherwise.
4. **`register N ✓` re-sends every grounded row** (potions, Horadric Cube, charms), not just the new ones from this sweep.
5. **Your v2346 ruling vs the live lifecycle.** An item read again in the INVENTORY 30 s or more after it was first held is committed to the vault (`vault:hold`), with no stash involved. v2346 was implemented only on a door that returns early for Chronicle names. Your call (VAULT-INTAKE-01 step 7).
6. **Routing of grounded magic/rare items.** By code reading, a rare ring or amulet parks in UNI-WEAPONS (*weapon — base: <name>*) or UNI-SMALL. MAGIC & RARE is reachable only for a rare circlet. Needs your ruling.
7. **The vault lane has banked nothing since about 2026-09-19.** The 45-second autoread cannot be relied on to pick up a test reel, so every scenario uses the manual sweep.
8. **Curly apostrophe.** *Atma's Scarab*, *Saracen's Chance* and *Cat's Eye* tag UNKNOWN instead of GRAIL. The vault fold returns the curly roster spelling, but the lexicon only holds the straight one.
9. **A sunder charm read with its base tail** (*Flame Rift Grand Charm*, *Renewed Rotting Fissure Grand Charm*) tags UNKNOWN. The grail backstop that holds throw-out suggestions misses it too.
10. **The magic/rare class lives only on UNSURE rows.** Owned rows, `apply_payload` and `/api/vault_ledger` all drop it. The board's *🔮 Magic & Rare* column is fed only by the AI item checker, so the two answers to "is this magic or rare?" are never compared.
11. **`/api/evidence` returns `witnesses: null` for every name.** `evidence_for` calls `counter_ledger.witnesses`, which does not exist; the function lives in `chronicle_retro`. Raven Claw, with 38 sightings, reads null.
12. **A hand tick never banks a `hand` witness.** The only UI caller of `/api/board_tick` sends `want:false`, and your evidence bank holds 0 manual rows.
13. **The monotonic peak is stale.** `ledger_peaks.json` foundLog reads 416 (from 2026-09-03) while the snapshots read 446, so a loss of up to 30 rows would read OK. Separately, uniques went from 312 to 309 on 2026-09-25, and nobody has explained why.
14. **A find ticked by the TV route is filed as "already had — nothing to do".** The ledger relabels every found row that was not accepted as *in-chronicle*. The routing summary also counts only the last 400 rows.
15. **Un-tick protection holds at 1 door out of 4.** The cross-reference, the sweep's register and `tvChronicleRoute` all tick without asking. A name that sits in both stores reads *in chronicle* everywhere.
16. **The agent banner's "film ON/OFF" defaults TV_FILM to 0, but the film thread defaults it to 1.** Your last banner printed "film OFF".
17. **`mini_start` always sends a focus.** So `focusChosen` is true even for the untouched preselected chip, and the defaulted-focus guard can never fire (REC-05 shows it).
18. **The rolling prune looks only at the oldest 120 aged frames and remembers nothing it kept.** Once 120 keepers pile up, newer frames are never examined for the rest of that session.
19. **REG-1284's failure caption is never seen.** It is written inside the theatre, and the same branch hides the theatre. Only the ui_fault records it.
20. **The End Session toast says *session saved · off air* even on the forced-kill path.** `sessionSaved` is always true, so the toast proves nothing about the seal.
21. **The capture-door Wilson ledger reaches no panel.** It is JSON on `/api/status` only: a candidate unjoined end.
22. **The Windows full-virtual fallback is labelled *🎯 Locked · Diablo II*** while the whole virtual screen is being filmed.
23. ✅ FIXED (REG-1304) - **Esc on the state panel, the fleet window, the heart panel or the receipts view closed it AND quit the console.** Their listeners do not stop the event, and the empty-console handler does not know those panels. The ✕ on the state panel is even titled *close (Esc)*.
24. **The doctor's fleet rows judge a second copy of the roster** (console_doctor imports control_app as a second module), and that copy refreshes only on periodic eagle passes. This comes from code reading and has not been measured. It would explain REG-1302's 55-59 min ages.
25. **`tv/.relaunch_receipt.json` `toVersion` is always null.** `_before_exec` never passes a version.
26. **Your uniques read 309 on the fleet card and 312 in the fleet cross-reference at the same minute.** Those are two numbers for one quantity, so a row cannot be checked against its board headline until one is chosen.
27. **The fleet machine word ignores `measuredBy`.** A never-synced ledger's 0 counts toward *differs*.
28. ***running code matches disk* ("PAGE changes are live") and *window runs the document on disk* ("older page") read as a contradiction when shown side by side.** Both are true.
29. **Two roster rows share the nickname GrokBot** (online v3504, offline v3377). The stale install may need pruning or a ruling.
30. **A quit's attribution is written only to stdout.** The Windows ALT (pythonw) drops stdout, so only the Mac can show who asked for a quit.

