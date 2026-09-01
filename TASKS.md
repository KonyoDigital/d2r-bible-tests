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

## 🔥 THE URGENT THREE — "task these in first urgently before the other tasks"

| # | What | State |
|---|---|---|
| **165** | **THE NEXT LOOK** — the harness has EYES AND NO HANDS. Synthetic pointer events need macOS Accessibility; without it `CGEventPost` silently succeeds and moves nothing. So Claude names the pane in CODE and a human eye photographs it. `tv/ask_view.py vault --brief HE-2` → `.view_request.json` → `view_request()` publishes 5 states on `/api/status` → the console honors it ONCE, stamps the screen, puts his tab back. Refused states (STALE/UNKNOWN/HELD/BROKEN) paint **nothing** on his screen. Contract = `gh #186`. | **SHIPPED v2399** |
| **166** | **LOCK THE NAMESPACE, and the ledger is authoritative.** His ruling: *"NO i want it locked to whats it is now"* / *"not only up — its also in the ledger with proof, that way from there it can reupdate its profile if needed"* / *"anything done manually by a human is proof and witness enough and bypassed."* PIN `I·77f64154·`, profile `main`. The law is **MONOTONIC** (may rise, never fall), not equality. | **BLOCKED — measured.** The loggers do not carry proof today: `d2r_foundLog` is 412 rows of `{name: "Jun 22, 2026 · 02:00"}`, a display string with no reel/frame/witness, and 8 of his 169 owned items have no log row at all. The rebuild he wants is right; the data cannot do it yet. |
| **167** | Show the eye in **THE FLEET** when it is live. | READY (after 165 lands) |

---

## ✅ READY TO APPLY — five, each already diagnosed

| # | What | Where |
|---|---|---|
| **135** | Daily-pick dead branch. 3 edits + 1 spec test. ⚠ Three namespaces use `'grail'`; **only the chron-entry key may change.** | `bible.html` |
| **143** | Delete `fv.onclick`, extend the panel's FLEET section. | `bible.html:12021` |
| **159** | Brief self-contradiction — the doc says `KEEP = 2 distinct sessions, THROW = 3 distinct recordings`; the code ships `KEEP_MIN_WITNESSES = 3` and `THROWOUT_MIN_WITNESSES = 4`. **And the semantics are wrong too:** KEEP counts *witnesses* (re-looks gated by `REOPEN_GAP_MS`, 3 min — three reads can come from ONE recording); only THROW passes `witness_field="session"`. Same defect Grok filed as **GB-B-1**. | `PROJECT_VAULT_MANAGER.md:69,71` vs `tv/vault_retro.py:163-167` |
| **153** | Register `hover_wilson` as a gate — **fail on LEAKS, never on UNPROVEN.** | `tv/run_gates.py` |
| **164** | Paint-witness invariant: `>=`, not `==`. | `tv/` |

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
| **GB-B-1** | `PROJECT_VAULT_MANAGER.md` still says KEEP=2 / THROW=3; the code ships 3 and 4. | **OPEN** — same as task **159**; fix once, close both. |
| **GB-B-2** | HOLDS *writers* are gated, but ~289 possession claims already sitting in `d2r_owned` are undone by no gate. | **OPEN** — cleanup, not an open door. ⚠ `d2r_owned` is TESTIMONY; only he may overrule his own ticks. |
| **GB-L-1** | HE-1 look — hovered cell matches tooltip item + true slot. | **UNKNOWN** 2026-09-01 — no `D2R.exe` on konyo-3. Re-run when the stash is open. |
| **gh #186** | The eye's half of task 165 — the contract for what Claude may ask an eye to photograph. | **OPEN** |
