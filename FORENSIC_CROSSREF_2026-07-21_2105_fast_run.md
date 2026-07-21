# FORENSIC CROSS-REF — Fast-run soak · 2026-07-21 21:05

**Mode:** READ-ONLY analysis (no code changes in this doc pass)  
**For:** Claude / SuperGrok cross-reference  
**Author:** Grok (xAI) · 2026-07-21  
**Repo stamp at analysis:** `v948.16` on `main` (`6be9440`)

---

## 1. Inputs aligned

| Source | Identity |
|--------|----------|
| **Desktop MOV** | `~/Desktop/Diablo II Screenshots/Screen Recording 2026-07-21 at 21.05.18.mov` |
| **Duration** | **157.4 s** (`ffprobe`) · file mtime ~21:07:56 |
| **TV session** | **`s_1784657116450_14249`** |
| **Journal span** | **21:05:20 → 21:08:20** (seal) · late receipts to **21:12:03** |
| **Film reel** | `tv/frames/hist/reel_s_1784657116450_14249/` · **153 × f_*.jpg** |
| **Film span** | **21:05:21 → 21:07:53** (**152.8 s**) |

**Alignment:** MOV filename 21:05:18 ≈ session start 21:05:20 ≈ first film 21:05:21. Duration ≈ film span (**±5s**). **Film lane is complete.**

---

## 2. Konyo’s thesis (what this run was for)

> Went **super fast on purpose**. First AI reader can’t keep up — that’s logical.  
> **As long as screenshots were taken**, aftermath layers (🔴 miss → 🔵 → 🧠 → 🚦 → 🛡 → ⚙️) should weed inaccuracy and ship verified reads **after** the session sleeps.

**Verdict on film:** ✅ Photos were taken. 0 film gaps >2s. Completeness log: **0 film drops · 153 reel frames**.

**Verdict on aftermath:** ⚠️ **Partial.** Some engines fired (vault-count, live-judge, runes tally, KAI gems+runes funnel). Others incomplete or silent (second-eye 0, materials 0, gems receipt missing, kai_report missing routing/register, Spirit grail→toss still wrong).

---

## 3. Layer-by-layer scorecard

### 🎞 CAPTURE (film ground truth) — **PASS**

| Metric | Value |
|--------|--------|
| Reel stills | **153** |
| Gap min/med/max ms | 617 / 1014 / 1726 |
| Gaps >2s | **0** (no FOOTAGE STARVE) |
| Completeness log | `153 reel frames · 0 film drops · 26.3% covered · 14 unread` |

**Covered % low is expected** on a speed-run: few deeps vs dense film. **Film completeness is the win.**

---

### 🔴 LIVE EYE (first deep reader) — **SLOW / SPARSE (by design of test)**

Only **7 deeps** in ~2.5 min of film:

| Clock | Scene / tab | Names (NEW) | Vision ms |
|-------|-------------|-------------|-----------|
| 21:05:23 | transition | — | **68978** (!!) |
| 21:06:35 | personal | Spirit Monarch | 11380 |
| 21:06:47 | personal | Sullied Grand Charm of Blight | 14949 |
| 21:07:04 | shared | Dread Whorl | 11268 |
| 21:07:17 | shared | Eagle Gorget | 10519 |
| 21:07:31 | shared | Ivory Jewel of Bliss | 9926 |
| 21:07:42 | runes | — (empty) | 8455 |

**All deep hist JPEGs on disk** (`1_`…`7_*.jpg`).

**Text-eye** fired hard (18 skips + OCR garble: `IA Lla`, `Ii`, lobby noise) — backlog pressure matches “I went too fast.”

**No materials / gems deep** — live never sticky-named those tabs.

---

### 🔵 SECOND EYE (verify / gap recheck) — **SILENT**

| Metric | Value |
|--------|--------|
| `lane=verify` rows | **0** |
| `#v` frames | **0** |

**Gap:** On a deliberately overloaded live path, second-eye queue did **not** land any journaled rechecks this session. Aftermath cannot claim 🔵 coverage for this run.

---

### 🔬 LIVE ITEM CHECKER (mid-session) — **FIRED (5/5 named NEW items)**

Control log:

```
🔬 live-judge: Spirit Monarch
🔬 live-judge: Sullied Grand Charm of Blight
🔬 live-judge: Dread Whorl
🔬 live-judge: Eagle Gorget
🔬 live-judge: Ivory Jewel of Bliss
```

| Item | Journal tier | Applied | Score | Assessment |
|------|--------------|---------|-------|------------|
| Spirit (Monarch truncated) | grail* | **toss** | 0 | **BUG** — still grail/toss split; Spirit≠unique |
| Sullied Grand Charm of Blight | border | border | 8 | OK hold |
| Dread Whorl | border | border | 12 | OK hold |
| Eagle Gorget | keep | keep / mule | 22 | OK keep |
| Ivory Jewel of Bliss | toss | toss | 1 | OK toss path |

\*Server/client grail-gate still polluted by bare runeword-ish “Spirit”.

---

### 🧰 ENGINE-DRIVER (live tallies while sleeping engines catch up)

| Tab | Kind | Total | When |
|-----|------|-------|------|
| personal | vault-count | **30** | 21:07:34 |
| shared | vault-count | **58** | 21:07:43 |
| runes | tally | **404** | 21:08:20 (**after** seal 21:07:53) |

Vault **count** lane worked under speed pressure. Runes live tally completed **post-seal** (never-zero / queue drain).

---

### 🧠 KAI CLOSER (post-seal full reel) — **SCANNED, INCOMPLETE LEDGER WRITE**

| Metric | Value |
|--------|--------|
| kaiVer | **3** (v948.7+ reclose generation) |
| Scanned | **153 / 153** |
| Classes (scan) | gameplay 28 · stash 98 · tooltip 7 · **stash-gems 2** · **stash-runes 12** · **materials 0** |
| Missed-text frames | 9 (OCR garble + partial tooltips) |
| **routing[] in kai_report** | **MISSING** (key absent) |
| **register in kai_report** | **MISSING** |
| Control log later | `routing: 153 frames, 1 fired` · register 3 · completeness line present |

**Interpretation:** Closer **did** walk every Theatre still and **did** start Stage-3 funnels, but the **persisted** `kai_report.json` is a **mid-write / partial seal** (no routing/register). Journal has KAI unread lines + close note; register propose logged `queued=0 from 3`.

#### Funnel aftermath (control log)

```
📸 KAI funnel (ledger): fired gems from f_1784657220125.jpg
📸 KAI funnel (ledger): fired runes from f_1784657272043.jpg
📸 KAI funnel: runes receipt journaled ✓
```

| Tab | Funnel fired? | Journal receipt this SID |
|-----|---------------|---------------------------|
| gems | YES (log) | **NO `kai-funnel` gems row found** |
| runes | YES | **YES** `kai-funnel` total=**4** @ 21:11:57 (after live tally 404 — **SET risk**) |
| materials | NO (0 class hits) | NO |

**Conflict:** Live runes tally **404** then KAI funnel SET’d to **4** — classic SET-wrapper overwrite if funnel photo was a partial/wrong runes still. **Accuracy gate / never-zero pin should prevent demolishing a good tally with a thin funnel shot.**

---

### 🚦 ROUTER + 🛡 ACCURACY GATE

- Completeness + register lines imply router ran in process memory.
- **On-disk routing empty** → Theatre gate badges / Claude offline audit of proven/held **cannot** use this reel’s `kai_report` alone.
- Session health earlier showed gate **91 proven / 19 held** from a *prior* seal — not this fast run’s durable artifact.

---

### 📖 CHRONICLE

```
📖 Chronicle propose: queued=0 from 3 register items
```

Likely all 3 already settled or auto-triaged; needs engine LS cross-check (not done this pass — READ-ONLY).

---

## 4. What the speed-run proved

| Claim | Result |
|-------|--------|
| Film survives speed | **YES** — 153 stills, no starve |
| Live deep will starve | **YES** — 7 deeps, 69s first, text-eye skip storm |
| Live-judge still attaches to NEW names | **YES** — 5 judges |
| Vault-count under load | **YES** — 30 / 58 |
| Post-seal KAI walks all film | **YES** — 153 swept |
| Post-seal funnel uses film | **PARTIAL** — gems+runes fired; materials never classified |
| Second-eye fills live gaps | **NO** this run (0 verify) |
| Durable routing ledger for Theatre | **NO** — kai_report incomplete |
| SET funnel won’t clobber good tally | **FAIL signal** — runes 404 → funnel 4 |

---

## 5. Gaps for Claude (read-only punch list)

### P0 — aftermath integrity
1. **kai_report must atomic-write routing + register + gate fields** after Stage-3 (today: scan-only file can remain if later stage errors).  
2. **Gems funnel fire without journal receipt** — find drop between `_ejs` fire and `/intake_result`.  
3. **Runes SET 404→4** — gate: do not SET-funnel if existing real tally total ≫ new total (or only gap-funnel when total==0).  

### P1 — layers that slept
4. **Second eye 0** under load — verify queue not draining / VERIFY_ON / budget=0 when flooded.  
5. **Materials 0 classes** — either tab not on film *or* classifier still maps materials→stash; sample `f_*` around 21:07 with human Theatre eye.  
6. **Spirit grail→toss** — bare name / runeword pollution still active on live-judge path.  

### P2 — cross-ref tooling
7. Script: `session_id + MOV duration → film span + deep timeline + funnel matrix` (this doc’s method).  
8. Theatre STORY should surface hand-off chips: `🔴 miss → 🧠 caught` for the 9 missed-text frames.

---

## 6. Timeline (compact)

```
21:05:18  MOV start (filename)
21:05:20  session boot · film arming
21:05:21–21:07:53  153 film stills (continuous)
21:05:20–21:07:48  text-eye skip/OCR storm (fast pan)
21:05:23  deep#1 transition 69s vision (slow)
21:06:35–21:07:31  5 item deeps + 5 live-judges
21:07:34  vault-count personal ×30
21:07:42  deep runes empty
21:07:43  vault-count shared ×58
21:07:53  session_end OFF · watchdog runes gap
21:07:53+ KAI closer 153 frames · gems+runes funnel fire
21:08:20  live runes tally ×404 (late)
21:11:57  kai-funnel runes ×4 (overwrites risk)
```

---

## 7. Bottom line for Claude

**Konyo’s architecture claim is half-validated on this soak:**

- ✅ **Film is the ground truth** and survived intentional speed.  
- ✅ **Some aftermath engines** ran (KAI scan, live-judge, vault-count, partial funnel).  
- ❌ **Not yet “every photo thoroughly verified and shipped”** — second eye silent, materials absent, gems receipt missing, routing ledger not durable, runes SET clobber.

**Do not “fix” by asking him to go slower.** Fix aftermath integrity so **slow vision + fast hands** still converges on film.

**Reclose path (agent OFF):**  
`POST /api/kai_reclose {"sessionId":"s_1784657116450_14249"}`  
then re-audit `kai_report.json` for routing/gate/register.

---

## 8. Artifact paths

```
MOV:     ~/Desktop/Diablo II Screenshots/Screen Recording 2026-07-21 at 21.05.18.mov
Session: s_1784657116450_14249
Reel:    tv/frames/hist/reel_s_1784657116450_14249/
Report:  tv/frames/hist/reel_s_1784657116450_14249/kai_report.json  (PARTIAL)
Journal: tv/sessions.jsonl  (filter sessionId)
Log:     tv/control_app.log  (lines ~4329–4345+)
```

---

*End forensic · READ-ONLY · for GitHub cross-ref with Claude*
