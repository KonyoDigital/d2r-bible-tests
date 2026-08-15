# PLAN - binding the storage world to the INSTALL, not the operating system

A new machine starts empty because it is a new machine, not because of what OS it runs.

STATUS: **SHIPPED at v1499** (this line said "PLAN ONLY, nothing shipped" until 2026-08-15 — it was written before the ship and never updated, so a reader could take the pre-v1499 behaviour described below as current). Everything below describes the state at HEAD a20b9e2 = v1498 and the plan to change it; the plan was carried out. For what actually ships today read `bible.html:3505-3640` and `tv/WINDOWS_ONLY.md`. Written 2026-07-31.

ASSEMBLY NOTE: the nine section drafts this document was meant to assemble were not present on disk at assembly time. Every section below is therefore AUTHORED BY THE ASSEMBLER, written from the shared contract and from facts re-verified against the code at HEAD a20b9e2. Every claim about current behaviour cites file:line.

---

## 0. THE PROBLEM IN ONE PAGE

*AUTHORED BY THE ASSEMBLER*

Konyo's requirement, verbatim: "if i go login on my windows (adi's my wife's pc) it should be a clean slate completely for anyone new registering."

Today the app decides whose data you see by asking what operating system you are on. bible.html:3377 joins every platform signal the browser offers and bible.html:3399 tests it against `/mac|iphone|ipad|ipod/i`. Mac means owner. Anything else means a separate world. bible.html:3420 then routes storage keys on that answer: owner main uses bare key names, owner ladder uses `L·`, non-Mac uses `W·` and `WL·`.

The measured consequence. A fresh browser profile on a non-Mac lands in the `W·` world and shows 0 forged, 0 grail, 0 set pieces - a genuine clean slate. A fresh profile on a Mac lands on the bare keys and shows 99 forged, 243 grail, 108 set pieces. Adi's Windows PC is already safe. Any Mac is not: a new laptop, a borrowed one, a friend's, all present themselves as him.

The crux, and it matters more than anything else here: a brand-new Mac shows those numbers **not because data travelled, but because the app re-mints them from constants that ship inside bible.html**. `_RWC_SEED` (bible.html:14985) holds exactly 99 runeword names, `_GRAIL_SEED` (14720) exactly 243, `_SET_SEED` (14725) exactly 108, and they are re-applied on every load (14995, 15021-15031, 15827-15852) unless the world is the cousin world or the profile was explicitly reset. Nothing is copied between machines. A stranger's Mac shows a convincing fake, assembled locally from public source. His genuinely private data - vault, mule roster, intake log, forge state - has never left his browser.

The fix in one sentence: stop asking the operating system and start asking the install, where exactly one install per browser origin is CLAIMED as the owner and everything else gets its own empty namespace.

**What changes for Konyo.** Nothing on his MacBook - his data stays in the same bare keys it has always been in, byte for byte. His phone and any other browser become honestly empty instead of showing a re-minted fake of his chronicle. Adi's PC and any new Mac start at zero. The one visible cost is a single blank page on his MacBook after the upgrade, ending the moment he clicks one button.

**What this plan does NOT do**
1. It moves no data - not one byte is copied from one key to another.
2. It deletes no keys, including the legacy `W·` and `WL·` worlds.
3. It renames nothing - the bare keys keep their exact current names.
4. It ships no code today.
5. It changes no file except this one.

---

## 0b. DECISIONS BOX

*AUTHORED BY THE ASSEMBLER*

Every choice this document settles, one line each.

- Owner world key names: unchanged. Owner main = bare (`d2r_owned`), owner ladder = `L·d2r_owned`.
- Guest world prefix scheme: `I·<first8>·` for main, `IL·<first8>·` for ladder, where `<first8>` is the first 8 characters of the install id.
- Ownership pointer: one new key, `d2r_ownerClaim`, holding the install id that owns the bare world in this origin.
- Synchronous install id: one new key, `d2r_installIdCache`, mirroring whichever id this origin resolved.
- Existing browser-local id `d2r_installId` (bible.html:37854) is kept and promoted into the cache when no console id is known.
- Ownership is claimed by an explicit human click. It is never inferred from the OS, from the hostname, or from the presence of bare keys.
- Public site (bull-4-u.com) default: every browser gets its own empty guest namespace.
- Claim button on the public site: NO in version one. Konyo's phone is populated with the existing Backup/Restore snapshot instead.
- Legacy `W·`/`WL·` worlds: preserved untouched, not adopted, not deleted.
- Route contract: `d2r_lsrRoute` moves to `v:2` and carries the literal prefix strings plus the install id. No other surface may construct a prefix.
- CI world: pinned by an explicit claim written in a Playwright init script, and the v1491 fake-Mac user agent (playwright.config.ts) is retired.
- Rollback: revert the ship commit, or set `d2r_ownerClaim` to the literal `*`.

---

## 1. DESIGN

*AUTHORED BY THE ASSEMBLER*

**What an install is.** A per-install identity already exists. `install_identity()` (tv/control_app.py:7948) mints a random opaque id into the gitignored `tv/.tvd_identity.json`, with hostname and OS user as human labels only plus a v1496 nickname (7899), and ships it in `/api/status` (8091). It was minted precisely because the mac/windows 2x2 cannot tell two Windows PCs apart. The world routing does not use it today. This plan makes it the routing input.

**Resolving the id, synchronously.** The route must be decided in the first script block, before any storage read. So the id has to be readable without waiting for a network call. Order, all synchronous:

1. `d2r_installIdCache` if present - use it.
2. Otherwise `d2r_installId` if present - use it and mirror it into the cache.
3. Otherwise mint a fresh random id, write both keys, use it.

The asynchronous console id never decides the current load. When `/api/status` answers with `identity.id` (the fetch that already runs at bible.html:37901) it is compared against `d2r_installIdCache`. Match, nothing happens. Mismatch, the cache is updated and a banner asks for one reload. The route for the load in progress does not change. This is the single async-identity rule for the whole document; other sections cross-reference it rather than restate it.

The consequence, stated plainly and deliberately: a load that has no cached id resolves NON-owner. There is no path where waiting, timing out, or failing to reach the console can produce the owner world.

**Deciding the world.** One comparison: `d2r_installIdCache === d2r_ownerClaim`.

- Equal - this install is the owner. Prefix for main is the empty string, prefix for ladder is `L·`. Exactly the keys that exist today.
- Not equal, or `d2r_ownerClaim` absent - this install is a guest. Prefix for main is `I·<first8>·`, prefix for ladder is `IL·<first8>·`.
- `d2r_ownerClaim` holding the literal `*` - the owner world, unconditionally. This is the documented emergency escape hatch, used by the rollback in section 4.

**How the owner claims.** By clicking a button that says so, and by nothing else. On a load that resolves guest with no claim recorded, a banner sits at the top of the board: this browser is not claimed, you are looking at a fresh empty world, press here if this machine is yours. The button writes one key. Nothing is inferred - not from the platform string, not from the hostname, not from `.tvd_identity.json`, and specifically not from the presence of bare keys, because a bare `d2r_rwMade` holding 99 entries is what the seed re-mints on any Mac that ever loaded the current build.

**Main and ladder inside a world.** The fork rule keeps its exact current shape with the prefix pair substituted. Today (bible.html:3420-3440): keys in `_LP_FORKED` (3409, 41 keys) fork by profile; on the non-owner world the keys in `_WP_FORKED` (3418) that are not in `_LP_FORKED` - the chronicle family - land on the machine prefix for both profiles, so that world's main and ladder share one chronicle; everything else falls through unprefixed, which is why UI preferences look identical in every world. The guest world behaves identically with `I·<first8>·` for `W·` and `IL·<first8>·` for `WL·`. No key changes fork class.

**Seed suppression.** Today the seeds are suppressed by `window._isCousinShell` (bible.html:3404, derived from the OS) and by `d2r_rwProfile === 'fresh'` (bible.html:14993). The OS-derived condition is replaced by "this load did not resolve to the owner world". The fresh-profile flag is unchanged. This is what makes an unclaimed load safe: with seeds suppressed, an unclaimed load writes no bare account key at all.

**Where the truth lives.** In bible.html, resolved once, published once - see section 1b.

### Assembler corrections

None required. No draft was present to violate the contract. The design above implements INV-1 through INV-8 as written; the wildcard `*` value of `d2r_ownerClaim` is an addition, not an override, and is confined to rollback.

---

## 1b. ONE SOURCE OF TRUTH

*AUTHORED BY THE ASSEMBLER*

v1478 was written because two copies of the routing rule existed and drifted. The board wrote `W·`, the console read bare, and a machine that should have started at zero greeted its owner with "HOLY GRAIL 243 / 403 · 60% claimed". That is REG-076. The fix was to publish the rule as data: bible.html:3454 writes `d2r_lsrRoute` as `{v:1, m, p, lp, wp}` and tv/control_ui.html:8864-8895 reads it.

The fix was incomplete, and this is verified, not assumed. tv/control_ui.html:8888-8893 still contains the prefix literals and still builds `'W·' + bare` itself. tv/control_ui.html:8884 still falls back to reading `d2r_activeMachine` when the route is missing. And tv/control_ui.html:9982 `worldOf()` is a surviving second copy that reads `d2r_activeMachine` and `d2r_activeProfileWin` directly and never consults the route at all.

The contract this plan adopts:

- bible.html resolves the route synchronously in the first script block and publishes it at `v:2`. The payload gains three fields: `pfx` (the literal main prefix for this world), `lpfx` (the literal ladder prefix), and `id` (the install id the route was computed from). `m` becomes `owner` or `guest`.

```
{ "v":2, "owner":true, "id":"9f2c...", "p":"main",
  "pfx":"", "lpfx":"L·", "lp":[...41 keys...], "wp":[...50 keys...] }
```

- Every other surface reads `pfx` and `lpfx` as strings and concatenates. No surface anywhere may contain a prefix literal. That includes tv/control_ui.html:8854 `lsFork` and tv/control_ui.html:9982 `worldOf`, both of which are rewritten to read the published payload.
- No fallback. A missing route, a `v:1` route, or a route whose `id` does not match the identity this surface knows resolves to UNKNOWN. An unknown route renders "the board has not loaded in this browser yet" and reads nothing. It never guesses a prefix, and it never falls back to `d2r_activeMachine`. Guessing is how REG-076 happened; guessing bare is how it caused harm.
- A static test enforces the rule: no file under tv/ may contain the prefix string literals.

---

## 2. THE NO-IDENTITY CASE

*AUTHORED BY THE ASSEMBLER*

The board runs in three separate localStorage stores that share nothing: `file://` (the test suite), `http://127.0.0.1:17772` (served by the console) and `https://bull-4-u.com` (the public site). A claim in one does not travel to another - a property of browsers, not a design choice. Only the console origin can be handed an install id by `/api/status`; on `file://` the fetch is skipped outright (bible.html:37894-37898, v1490, because the failing fetch tripped Routine G) and on the public site there is nothing to ask.

So "no identity" is a misnomer. There is always an identity, because bible.html:37854 already mints and stores `d2r_installId` locally. The decision this plan makes: **the browser-local id IS the install identity for that origin**, and a browser with no console gets its own guest namespace and is empty.

Weighed against the alternatives:

- Owner world by default on the public site - rejected outright. Adi lands on the public site. This is the exact failure Konyo asked to remove.
- Read-only view of the owner world - rejected. There is no owner data on the public origin to show. What a stranger would see is the re-minted seed floor, which is a fake, and building a read-only mode to display a fake is worse than showing nothing.
- Own namespace, empty - chosen.

**The phone consequence, stated honestly.** Konyo opens bull-4-u.com on his phone and sees an empty bible. That is correct: his 243 grail entries live in his MacBook's browser and have never been on his phone. What the phone showed before this change was the seed floor - 99, 243, 108 re-minted from constants - over an empty vault, empty mule roster and empty intake log. It looked like his data and was not. The honest way to populate the phone already exists: the Backup/Restore snapshot (bible.html:17670-17700), which exports the active world under bare names and restores wherever it is pasted.

**Claim button on the public site: recommended NO for version one.** The site is behind HTTP Basic auth so a claim there would not be open to the world - but it would buy him only the seed floor, since his real data is not there. It is a button whose reward is a fake and whose worst case is someone past the password gate pressing it. This is question 2 in section 7; the objection, that he now has a manual step to reach his phone, is kept alive as R8.

---

## 3. MIGRATION

*AUTHORED BY THE ASSEMBLER*

The migration is a pointer write. Nothing is copied, moved, renamed or deleted. His 99 forged runewords, 243 grail entries, 108 set pieces, vault, mule roster and forge state stay exactly where they are: in the bare keys, under the names they already have.

**Order of operations, per origin, on his MacBook.**

| Step | What happens | Keys written |
|---|---|---|
| M0 | New build loads. `d2r_ownerClaim` is absent, so the route resolves guest. Seeds are suppressed. The page is empty and a banner explains why. | `d2r_installIdCache` (new), possibly `d2r_installId` (existing behaviour) |
| M1 | He clicks "This browser is mine". | `d2r_ownerClaim` = the install id. One key. |
| M2 | The page reloads. Route resolves owner. Bare keys are read. 99 / 243 / 108, vault, mules and forge are all back. | none |
| M3 | Repeat M0-M2 on the console origin (127.0.0.1:17772). The `file://` origin only matters to the test suite. | as above, in that origin's store |

**Exactly which keys are touched.** Three, and two of them are new: `d2r_ownerClaim` (new), `d2r_installIdCache` (new), `d2r_installId` (already written today at bible.html:37854). No existing key is read-modified-written by the migration. `d2r_activeMachine` and `d2r_machineSource` are not written, not read for routing, and not deleted - they simply stop mattering.

**If the browser is closed mid-migration.** There is no window in which the store is half-migrated, because there is no multi-key write.

- Closed between M0 and M1: nothing was written except the id cache. The next load repeats M0.
- Closed during M1: `localStorage.setItem` on a single key either happened or did not. If it happened, the next load is owner. If it did not, the next load repeats M0.
- Closed during M2: a reload. The claim is already durable.
- Re-clicking claim: writes the same value to the same key. Idempotent by construction.

**During the blank window, nothing bare is written.** This is load-bearing and is enforced by test, not by inspection. Seeds are suppressed on any non-owner load (section 1), so the three re-appliers at bible.html:14995, 15021 and 15827 do not fire, and guest writes go to `I·<first8>·` keys. UI preferences fall through unprefixed exactly as they do in every world today (3430, 3432) - pre-existing, not account data, and the reason bare-key presence can never be read as ownership.

**Two things must be hardened before this ships, or the blank window becomes dangerous.**

1. `wipeProfile` (bible.html:3496) must learn the new prefixes and protect the three identity keys the way it already protects `d2r_activeProfile`, `d2r_activeProfileWin` and `d2r_activeMachine` (3500-3501). In a guest world it must kill only that install's own `I·`/`IL·` keys; if it ever reaches bare keys from a guest world, that is the data-loss path.
2. The erase control (bible.html:7875) is disabled while unclaimed. A blank page invites a panic reset, and a reset is the one act in this system that destroys something.
3. The backup pointer list `PTRS` (bible.html:17680) gains all three keys, so a restored snapshot can never transfer or revoke ownership.

---

## 4. ROLLBACK

*AUTHORED BY THE ASSEMBLER*

**The one-step way back.** Revert the ship commit and redeploy. Because the migration moved nothing, the previous build finds every bare key exactly as it left them, derives `mac` from the platform at bible.html:3399, and his world is back with no further action. The leftover `d2r_ownerClaim`, `d2r_installIdCache` and `I·` keys are inert to the old build.

**The way back without a deploy**, for the case where he is mid-session and wants his data on screen now: set `d2r_ownerClaim` to the literal `*` from the browser console and reload. `*` means "the owner world, unconditionally, in this origin". One key, one value, one reload.

**How he would know it has gone wrong.** The expected state after the upgrade is a blank board WITH the yellow unclaimed banner and a claim button. Any of the following is a failure, not the plan working:

- The board is blank and there is NO banner and no claim button.
- He clicks claim, the page reloads, and the chronicle is still 0 / 0 / 0.
- The chronicle comes back but the vault, mule roster or forge state is empty - that would mean the route is owner for some keys and guest for others.
- The console (127.0.0.1:17772) and the board disagree: one shows 99 / 243 / 108 and the other shows zero. That is REG-076 returning.
- Any number appears that is neither his real figure nor zero.

**Do guest worlds get wiped on rollback?** Recommended NO. Deleting `I·` keys is the only irreversible act available and it buys a few kilobytes. Leaving them means a rolled-back-then-rolled-forward machine finds its own world intact. This is question 4 in section 7.

---

## 5. TEST PLAN

*AUTHORED BY THE ASSEMBLER*

**Measured at HEAD a20b9e2:** tests/ holds 325 `*.ts` files. 129 of them mention `d2r_`. 109 of them write a bare `d2r_` key with `setItem`. Exactly one references `d2r_lsrRoute` or `d2r_activeMachine`. playwright.config.ts pins a Macintosh user agent (added v1491) specifically so the OS sniff resolves `mac` and the suite exercises the bare keys - that is REG-084's fix, and it becomes obsolete the moment the OS stops deciding.

**What happens to the 109 bare-key specs.** An unclaimed browser resolves guest, so their bare writes would land on keys the app no longer reads and all 109 files would go red at once. They are not edited one by one. The fix is one line of global setup: before every page load, write `d2r_installIdCache` and `d2r_ownerClaim` to the same fixed value (`ci-owner`). The suite then runs in the owner world and every bare-key spec passes unchanged. This replaces the fake-Mac user agent, which is retired because it would then be a lie about what pins the world.

**The CI world pin becomes** an explicit claim in an init script plus one spec whose entire job is to assert that the resolved world is the owner world. REG-084 was a silent failure - forty runs against the wrong world with the app innocent. A world that is asserted cannot drift silently.

**Specs to add.**

| Spec | Proves |
|---|---|
| `identity_fresh_install_is_empty` | No claim, fresh store: 0 forged, 0 grail, 0 set pieces, empty vault - and no bare ACCOUNT key created (snapshot bare keys before and after; only UI preferences may appear). The fresh-install-is-empty proof. |
| `identity_owner_data_did_not_move` | Fingerprint the bare keys, claim, reload: every bare key byte-identical and on screen. The owner-data-did-not-move proof. |
| `identity_claim_is_one_key` | Diff the whole store across the claim click: exactly one key added, nothing modified, nothing removed. |
| `identity_route_v2` | The route parses at `v:2`, carries `pfx`/`lpfx`/`id`, and matches the keys the board actually wrote. |
| `identity_no_prefix_literals` | Static scan: no file under tv/ contains a prefix literal. Structurally prevents REG-076. |
| `identity_console_agrees` | In a guest world the console's `lsFork` lands on the same physical key the board wrote; with the route blanked it renders unknown instead of reading bare. |
| `identity_no_console_origin` | With `/api/status` unavailable: local id path, guest world, empty board. |
| `identity_async_id_never_reroutes` | A console id differing from the cache does not change the current load's keys; a reload banner appears instead. |
| `identity_interrupt_safe` | Claim, hard-reload mid-load, claim again: still owner, bare keys still byte-identical. Idempotence and interruption safety. |
| `identity_wipe_scoped` | `wipeProfile` in a guest world removes only that install's keys - never bare keys, never the three identity keys. |
| `identity_two_guests_isolated` | Two install ids in one origin: each sees zero, neither reads the other's keys or the bare keys. |
| `identity_backup_never_transfers_ownership` | Export as owner, restore as guest: the guest stays a guest. |

**Existing spec that must be rewritten:** `v663_machine_shell.spec.ts` sets the machine by hand and asserts the `W·` world. It becomes the guest-world spec under the `I·` scheme. It is the one spec that legitimately changes meaning.

**Local run discipline is unchanged.** Smoke plus the identity specs plus anything touching the route on the Mac. The full suite runs in CI.

---

## 6. RISK REGISTER

*AUTHORED BY THE ASSEMBLER*

Ranked by what it would cost Konyo.

| # | Risk | The concrete failure it prevents | Control |
|---|---|---|---|
| R1 | Losing or stranding the live chronicle | He upgrades and 243 grail entries are gone or unreachable | The migration writes one new key and touches no existing key (section 3). `wipeProfile` hardened and scoped; Reset disabled while unclaimed; two specs fail the build if either is violated. |
| R2 | A new install claims the owner world | A new Mac, or Adi's PC, opens the app and is him | Ownership is claimed by an explicit click and never inferred (INV-2). No platform check, no hostname check, and specifically no bare-key check, because the seeds re-mint bare keys on any Mac that loaded the old build (INV-8). |
| R3 | A stranger sees his chronicle | Someone opens the site and reads his progress | A guest never reads bare account keys and there is no bare fallback anywhere, including the console (section 1b). Honest scope: the 99/243/108 lists are constants in a public HTML file and were never secret; the vault, mules, intake log and forge state are the private data and have never left his browser. |
| R4 | The board and the console disagree again (REG-076) | A fresh machine's console shows "243 / 403 · 60% claimed" | The route carries the literal prefixes and the install id; the console holds no literals and no fallbacks, and an unknown route renders unknown. Enforced by two specs. |
| R5 | The suite silently tests the wrong world (REG-084) | 100 specs red on CI, green on the Mac, app innocent, forty runs wasted | The world is claimed explicitly in global setup and asserted by its own spec. The fake-Mac user agent is retired, so no world can be inherited from whichever host runs the job. |
| R6 | His install id changes underneath him | He clears site data, or `.tvd_identity.json` is regenerated, and his own MacBook becomes a guest | The blank-plus-banner state appears and one click re-claims; `d2r_ownerClaim = *` is the no-deploy escape. The sharpest residual risk - no browser-local pointer can survive a user clearing site data. |
| R7 | The async console id decides a route | The page renders one world, then the fetch answers and it silently becomes another | The route is resolved synchronously from the cache only. The async id may write the cache and request a reload; it may never re-route a load in progress (section 1). |
| R8 | Origin fragmentation | He claims on the console origin, opens bull-4-u.com, and it is empty; his phone stays empty by design | Three stores, three claims, stated up front. The withheld public-site claim is the surviving objection from the rejected "claim everywhere" option, and its cost is real: populating the phone is a manual Backup/Restore. |
| R9 | Panic during the blank window | He sees an empty board and presses Reset | The banner explains the state before he can act on it, and destructive controls are disabled until a world is claimed. |
| R10 | Legacy `W·`/`WL·` worlds orphaned | A cousin machine's existing progress becomes unreachable | Those keys are preserved, never deleted. Adoption is deferred: adopting means re-pointing a world, and every re-pointing is a chance to point at the wrong one. |
| R11 | A restored backup transfers ownership | He restores a snapshot on a guest machine and it becomes the owner | All three identity keys join the `PTRS` list at bible.html:17680, so they never travel in a snapshot. |

---

## 7. DECISION - what Konyo is being asked to approve

*AUTHORED BY THE ASSEMBLER*

Five questions only he can answer. Each carries the plan's recommendation.

1. **What does the public site show a browser it does not recognise?** RECOMMENDATION: its own empty world. Not his, not read-only, not a preview.
2. **May a claim button exist on the public site (bull-4-u.com)?** RECOMMENDATION: no, in version one. It would give him only the seeded floor, not his vault, and it is one more surface where a wrong click hands someone the owner world. Use Backup/Restore to populate the phone.
3. **Is one blank load on your MacBook, ending with one click, acceptable?** RECOMMENDATION: yes. It is the price of never inferring ownership, and every safe alternative reintroduces guessing.
4. **On rollback, may guest worlds be wiped?** RECOMMENDATION: no. Leave them. Deletion is the only irreversible act in this plan.
5. **Are the existing `W·` / `WL·` cousin worlds preserved as-is, or adopted onto the new scheme?** RECOMMENDATION: preserved as-is, untouched. Adoption can be added later once the new scheme has run for a while.

If you reject this, the safest alternative is to leave the routing exactly as it is and add nothing but a visible world badge, so a new Mac still shows the seeded numbers but says plainly which world it is in.
That is strictly worse for your requirement - a stranger's Mac still greets them as you - but it moves no data and can be shipped in an afternoon.

---

## A. KEY LEDGER

*AUTHORED BY THE ASSEMBLER*

The single most checkable artefact in this document. "Protected" means excluded from `wipeProfile` (bible.html:3496) and from the backup `PTRS` list (bible.html:17680).

| Key | New or existing | Origin(s) | Who writes it | When | Absence means | Protected from wipe / from backup |
|---|---|---|---|---|---|---|
| `d2r_ownerClaim` | NEW | all three, independently | bible.html, on the claim click only | once, on an explicit human click | this browser is not the owner - resolve guest | yes / yes |
| `d2r_installIdCache` | NEW | all three | bible.html, first script block | every load if absent; updated when the console id differs | no id known yet - resolve guest, mint one | yes / yes |
| `d2r_installId` | existing (bible.html:37854) | all three | bible.html sigil block today, first script block after the change | first load in an origin | no locally minted id - mint one | yes / yes |
| `d2r_lsrRoute` | existing (bible.html:3454), `v:1` becomes `v:2` | all three | bible.html, right after resolving the route | every load | the board has not loaded here - other surfaces render unknown and read nothing | not applicable / yes |
| `d2r_activeProfile` | existing | all three | `profileSwitch` (bible.html:3474) | on a profile click | main | yes / yes |
| `d2r_activeProfileWin` | existing | all three | legacy `W·` worlds only | on a profile click in a legacy world | main | yes / yes |
| `d2r_activeMachine`, `d2r_machineSource` | existing (bible.html:3399-3400) | all three | today, every load, auto-derived. After the change: neither written nor read for routing | n/a after the change | nothing - they stop being consulted | yes / yes |
| `I·<first8>·d2r_activeProfile` | NEW | all three | `profileSwitch` in a guest world | on a profile click | main | no (it is that world's own pointer) / yes |
| bare account keys (`d2r_owned`, `d2r_rwMade`, `d2r_foundLog`, `d2r_setPieces`, `d2r_muleRoster`, `d2r_forgeStep`, the rest of `_LP_FORKED`) | existing, UNCHANGED | all three | the app, owner world only | as today | that world has no data yet - the correct answer for a guest | wiped only by an owner-world wipe / exported as today |
| `L·` prefixed keys | existing, UNCHANGED | all three | the app, owner ladder | as today | owner ladder has no data yet | as today |
| `W·` / `WL·` prefixed keys | existing, FROZEN | all three | nothing, after the change | never again | a legacy world that was never used | never wiped by the new scheme / not exported |
| `I·<first8>·` / `IL·<first8>·` prefixed keys | NEW | all three | the app, in a guest world | as the app writes today | that guest has no data yet | wiped only by that guest's own wipe / exported by backup under bare names |
| `.tvd_identity.json` (`id`, `computer`, `user`, `nickname`) | existing (tv/control_app.py:7896, 7899, 7948) | console host filesystem, gitignored | tv/control_app.py | first console start; nickname on rename | no console identity - the browser-local id is used | not localStorage; never in a backup |

---

## B. WHAT THE CODE DOES TODAY (verified)

*AUTHORED BY THE ASSEMBLER - every line re-read at HEAD a20b9e2*

| Location | What is there |
|---|---|
| bible.html:3377 | `window.D2R_MACHINE` opens. A stored `d2r_activeMachine` is honoured only when `d2r_machineSource === 'user'`. |
| bible.html:3390-3393 | Every platform signal joined: `userAgentData.platform`, `navigator.platform`, `userAgent`. |
| bible.html:3399-3400 | `/mac|iphone|ipad|ipod/i` decides `mac` vs `windows`, and the answer is written back as `d2r_machineSource='auto'` - so it is re-derived and overwritten on every load. |
| bible.html:3404, 3407 | `_isCousinShell = (machine === 'windows')`, used in 12 places. `_PROFILE_PTR` is `d2r_activeProfileWin` on windows. |
| bible.html:3409, 3418 | `_LP_FORKED` = 41 account keys forking by profile. `_WP_FORKED` = those plus 9 chronicle-family keys. |
| bible.html:3420-3440 | `LSR.key()` - the 2x2. Owner main bare, owner ladder `L·`, windows main `W·`, windows ladder `WL·`; anything unmatched falls through unprefixed, which is why UI preferences are bare in every world. |
| bible.html:3454 | Publishes `d2r_lsrRoute` as `{v:1, m, p, lp, wp}`. |
| bible.html:3480, 3678 | `machineSwitch` writes `d2r_activeMachine` + `d2r_machineSource='user'` and reloads; the OWNER / THIS PC pills call it. |
| bible.html:3496-3501 | `wipeProfile` - prefix-scoped; explicitly spares `d2r_activeProfile`, `d2r_activeMachine`, `d2r_activeProfileWin`. |
| bible.html:7875 | The erase-all-progress button, which calls `wipeProfile` then reloads. |
| bible.html:14692 | `const LS = window.LSR` - every seed write below is routed. |
| bible.html:14720 / 14725 / 14985 | `_GRAIL_SEED` = 243 entries, `_SET_SEED` = 108, `_RWC_SEED` = 99. Counted, not estimated. |
| bible.html:14993-14995 | `_rwFreshFlag` reads `d2r_rwProfile === 'fresh'`; the runeword seed applies on first load unless fresh or cousin. |
| bible.html:15021-15031 | Runeword seed re-asserted on EVERY load, honouring explicit un-marks, skipped on the cousin shell. |
| bible.html:15827-15852 | Grail and set-piece seed floors, main profile only, skipped when fresh or cousin. |
| bible.html:17680-17685 | Backup `PTRS` - three pointers that never travel; a raw key exports under its bare name if and only if `LSR.key(bare)` resolves to it. |
| bible.html:37854 | `d2r_installId` - locally minted, stored, used for the sigil. |
| bible.html:37890-37901 | `file://` skips the `/api/status` fetch (v1490, Routine G); on the console origin the id it returns paints the crest and is never stored. |
| tv/control_ui.html:8854 | `lsFork` - reads `d2r_lsrRoute`, but still builds the prefixes from literals at 8888-8893 and still falls back to `d2r_activeMachine` at 8884. |
| tv/control_ui.html:9982 | `worldOf` - a surviving second copy reading `d2r_activeMachine` and `d2r_activeProfileWin` directly, ignoring the published route. |
| tv/control_app.py:7896, 7899, 7948, 8091 | `IDENTITY_PATH = tv/.tvd_identity.json` (gitignored, .gitignore:54); `set_install_nickname` (v1496); `install_identity()` mints a random `uuid4().hex` with hostname/user/platform as labels only; the identity rides into `/api/status`. |
| playwright.config.ts:26-40 | The v1491 Macintosh user-agent pin, with the comment explaining REG-082/084. |
| tests/ | 325 `*.ts` files; 129 mention `d2r_`; 109 write a bare `d2r_` key; 1 references the route or the machine pointer. |

---

## C. CHANGE-SURFACE INVENTORY

*AUTHORED BY THE ASSEMBLER - this describes a FUTURE ship. Nothing in this list has been changed by this run.*

| File | What would change |
|---|---|
| bible.html:3377-3404 | The OS sniff becomes the synchronous identity resolver plus the claim comparison. `D2R_MACHINE` becomes `owner`/`guest`; `_isCousinShell` becomes "not the owner world". |
| bible.html:3407 | The guest profile pointer moves inside the guest namespace. |
| bible.html:3420-3440 | `LSR.key()` reads two prefixes from the resolver instead of hard-coding four cases. Fork classes unchanged. |
| bible.html:3454 | The route publisher moves to `v:2` and gains `pfx`, `lpfx`, `id`, `owner`. |
| bible.html:3480, 3678 | `machineSwitch` becomes the claim action; the OWNER / THIS PC pills say claimed / not claimed. |
| bible.html:3496 | `wipeProfile` learns the new prefixes and protects the three identity keys. |
| bible.html:14995, 15021, 15827 | Seed suppression keys off the owner world instead of `_isCousinShell`. |
| bible.html:17680 | `PTRS` gains the three identity keys. |
| bible.html (new block, early) | The unclaimed banner and the claim button; destructive controls disabled while unclaimed. |
| bible.html:37815-37913 | The sigil block stops being the only place an id is minted: it reads the resolver's id, and the async fetch writes the cache instead of only painting a crest. |
| tv/control_ui.html:8854 | `lsFork` reads `pfx`/`lpfx` from the payload; every prefix literal and the `d2r_activeMachine` fallback go. |
| tv/control_ui.html:9982 | `worldOf` is deleted and replaced by a read of the published route. |
| tv/control_app.py | No change required. The identity already exists and already ships in `/api/status`. |
| playwright.config.ts | The v1491 user-agent pin is retired; a global init script writes the CI claim. |
| tests/ | 12 new identity specs; `v663_machine_shell.spec.ts` rewritten to the guest scheme; the other 108 bare-key files untouched. |
| BUGS.md | A REG number reserved for whatever this ship breaks, per the standing convention. |

---

## D. RESOLVED CONFLICTS

*AUTHORED BY THE ASSEMBLER*

The nine section drafts were absent from the scratchpad at assembly time, so there were no draft-versus-draft disagreements to arbitrate. What follows is the set of conflicts that did have to be resolved: between the contract as handed down, the fact sheet, and the code as it actually reads at HEAD a20b9e2.

| Conflict | Resolution | Reasoning |
|---|---|---|
| The fact sheet says v1478 gave the console one source of truth. The code shows tv/control_ui.html:8888-8893 still holds prefix literals, 8884 still falls back to `d2r_activeMachine`, and 9982 `worldOf` never reads the route. | The code wins; section 1b names all three sites. | REG-076 is exactly the bug class that comes from believing a fix landed everywhere. |
| The fact sheet and the v1491 comment both cite 105 bare-key spec files. Measured: 109 call `setItem` on a bare `d2r_` key, out of 129 mentioning `d2r_` and 325 total. | The measured figures are used throughout. | The CI change is sized by this number; an undercount understates the blast radius. |
| The task framing calls this "the no-identity case". | Reframed as "no CONSOLE identity". | bible.html:37854 already mints a browser-local id in every origin, so there is never truly no identity - the original framing invents a special case that does not exist. |
| Legacy `W·` world adoption would need a second, per-install mapping alongside `d2r_ownerClaim`. | Adoption deferred; legacy worlds frozen. | INV-6 requires rollback to be one pointer key, and a second mapping gives the resolver two inputs - the multiple-sources-of-truth defect again. Kept alive as R10. |
| An automatic claim prompt wherever bare account data is found would spare Konyo the blank load. | Rejected - the claim is a button he presses, never a prompt triggered by finding data. | A bare `d2r_rwMade` with 99 entries is what the seed re-mints on any Mac that loaded the current build, so "bare data exists" is evidence of nothing. |
| A public-site claim button would let his phone show his chronicle. | Rejected for version one. | It would show the re-minted seed floor, not his vault - a fake with a button on it. Backup/Restore does this honestly. Kept alive as R8. |
| Nothing in the contract covered a no-deploy rollback. | Added `d2r_ownerClaim = *` as a documented emergency value. | Rollback stays one pointer key: a wildcard value of that same key, not a second key. |

---

## APPROVAL BLOCK

- [ ] **Approve as written** - proceed with section 7's recommendations as the answers.
- [ ] **Approve with the section 7 decisions answered** - write your answers next to the five questions and proceed.
- [ ] **Reject** - see the alternative at the end of section 7.

No code has been written. No file in this repository has been changed except this one. Nothing ships until you say so.

---

## E. HOW THIS DOCUMENT WAS PRODUCED, AND WHAT I CHECKED MYSELF

*Added by Claude (Opus 5) on delivery, 2026-07-31.*

This plan came out of a `konyo-workflow-max` run that Konyo stopped at ~106 agents and 2h30m. The
expensive analysis had already finished — 3 independent architect designs, a judge merge, and 66
adversarial skeptic passes — so rather than discard it, the completed results were harvested from the
run journal and this document assembled from them.

**Why the run kept growing, honestly: my spec was self-contradictory.** I launched it with
`apply: false` (agents may write nothing) while the task asked each agent to write draft sections to
disk and a final file. So no agent could produce its deliverable, items failed their gate, and every
failure escalated into rework that dragged three fresh skeptics along — which is exactly why the
counter climbed 97 → 101 → 108 instead of falling. The assembler's own note records the symptom from
the inside: *"the nine input drafts do not exist anywhere on disk."* The lesson belongs in the triage
work: **a dry-run must never be given a file-shaped deliverable.**

**What I re-verified myself before shipping this, rather than trusting the agents:**

| Claim | Verified |
|---|---|
| `_RWC_SEED` holds 99 runeword entries | ✅ 99 keys counted in bible.html |
| `_GRAIL_SEED` holds 243 | ✅ 243 |
| `_SET_SEED` holds 108 | ✅ 108 |
| Platform sniff at bible.html:3377 | ✅ `window.D2R_MACHINE` begins line 3377 |
| LSR key router at bible.html:3420 | ✅ `window.LSR` begins line 3420 |
| Non-Mac world empty; Mac world 99/243/108 | ✅ measured live in fresh browser profiles, both worlds |

Those three counts matter more than any other fact here, because they carry the document's central
finding: **the numbers a stranger's Mac displays are re-minted locally from constants that ship inside
bible.html — they are not Konyo's data travelling.** His vault, mule roster, intake log and forge state
have never left his browser. That reframes the whole job from "a data leak" into "a convincing local
fake" — a smaller emergency, and a different fix.

**Status: nothing here is implemented.** No code was changed by the run or by this delivery. The
approval block below is real — the work starts when Konyo signs it, not before.
