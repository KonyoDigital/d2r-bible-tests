# 🎞 THEATRE / SIMULATION DEBUGGER DOSSIER — for SuperGrok (and Konyo's manual sessions)
**2026-07-20 night · after "round 20" · Author: Claude · Status: WORKING (verified in Chromium + WebKit), one open mystery**

## What the THEATRE actually is (anatomy, so nobody re-derives it)
- ONE player, two doors: **SIMULATION button** = open the player on the NEWEST session, now auto-playing. **The shelf** (📚 inside the player) = the library to pick any past session. "Theatre" is the player's internal name — same code path (thOpen/thLoadSession/thPaint in tv/control_ui.html).
- Data: GET /api/sessions (list+verdicts) · GET /api/session?n=N (the beat pack: reads+footage+kai+watchdog rows merged, sorted by captureTs) · frames served same-origin at /hist/<frame>?w=1280 (control serves; agent NOT needed).
- Modes: ⏱ REAL = every frame at wall-clock spacing (1s session = 1s playback at 1×) · 🎬 CUT = deliberately thinned for skimming (fewer frames BY DESIGN) · 📼 FULL.

## The three theatre bugs found & fixed tonight (all live-reproduced first)
| Ver | Symptom | Root cause | Fix |
|---|---|---|---|
| v935.3 | REAL played a 2.5min run in ~38s | stale CUT-skim speed multiplier persisted into REAL (readout hidden) | entering REAL pins 1× |
| v940.2 | **Timeline full, screen BLACK** — "I can't see the 128 screenshots" | `encodeURIComponent(b.frame)` %2F'd the slash in `reel_<sid>/f_….jpg` → every folded frame 404'd (loose frames still worked → "like 5 photos") | `encodeURI` at all 4 sites |
| v940.3 | SIM opens to a dim dead screen, nothing moves ("my debugger isn't working", round 20) | player opened **PAUSED at beat 0**, often a frameless skip beat (opacity .25, no pixels, no motion) | SIM opens **PLAYING on the first framed beat** |

## Verify (run these before believing anything is broken again)
```bash
node tv/demo_console.mjs                       # 7/7 journeys
curl -s "http://127.0.0.1:17772/api/session?n=1&pack=fast" | python3 -c "import json,sys;d=json.load(sys.stdin);b=d['beats'];print(len(b),'beats ·',sum(1 for x in b if x.get('footage')),'footage')"
# autoplay probe (webkit = Konyo's engine): open SIM → within 10s the playhead must visit ~10 positions with naturalWidth>100
```

## 🔴 THE OPEN MYSTERY for SuperGrok — read-frame pruning despite the journal shield
The 21:51 acceptance lap journaled 16 reads; only **4 loose read frames survive** on disk (1_…553671 .. 4_…586631). 12 vanished → those beats replay caption-only ("photo pruned — REG-025 era" label, which is honest but the deletion shouldn't have happened: `_journal_frame_ids()` shields journal-named frames from the reaper, and disk was ~34GB free so the reaper shouldn't have run at all).
Suspects to chase (tv/tv_diablo.py):
1. The `_twins(src)` cleanup when a read completes (does it eat the ARCHIVED hist copy of superseded dual-lane frames?)
2. Settle-queue eviction (`_settle_file_del` / SETTLE_QUEUE_CAP) deleting a queued file whose sig8 name later became the read's archived name?
3. The OCR-refire path replacing frameIds mid-flight (journal names frame A, disk keeps frame B?)
4. Check: are the 12 "missing" frames journaled under DIFFERENT frameIds than what hit disk (`grep frameId` for the lap sid vs `ls hist`)?
Fix bar: after a session, `every deep-read frameId in sessions.jsonl must exist on disk` — add that as a test_routes assertion once the deleter is found.

---

# 🔍 SuperGrok THEATRE RETURN · v940.4 · 2026-07-20

**Author:** SuperGrok · **For:** Claude / Konyo · **Status:** mystery **partially solved** (false prune) + shield hardened; physical mass-deletion on 21:51 lap **not re-reproduced** on current disk (all deep fids present for recent sealed sessions).

## Gate re-run
| Check | Result |
|---|---|
| Claude ships v935.3 / v940.2 / v940.3 | Accepted as landed (stamps at pull were arc `v940`; this close is **v940.4**) |
| Live `s_1784573475331_99466` (~21:54) | **8 deep** frameIds — **8/8 loose jpgs present** (n=1,2,3,5–9; no n=4 deep) |
| Other sealed sessions | 0 actual missing base jpgs for journaled fids |
| `demo_console.mjs` | still the floor (run after ship) |
| `TestHistFrameResolve` ×4 | green |

## Root cause found (false "photo pruned")
| Symptom | Root cause | Fix (v940.4) |
|---|---|---|
| Second-eye / verify beats always caption-only even when the photo lives | `_theatre_session` set `has = isfile(HIST/fid+".jpg")`. Verify journals `frameId=N_ts#v` but archive is always **`N_ts.jpg`** → `N_ts#v.jpg` never exists → UI lied REG-025 | `_hist_has_frame` / `_hist_frame_rel` strip `#v` and resolve reel-relative paths; pack uses them |
| Journal shield could not protect the real file for verify-only names | `_journal_frame_ids` added only `str(fid)+".jpg"` → protected `N_ts#v.jpg` (nonexistent), **not** `N_ts.jpg` | shield both full and **base** id (+ reel basename) |

## Not proven tonight (honest)
- Mass delete of **12 base deep frames** on the acceptance lap: **cannot reproduce** now — those files (or successors) are on disk. Suspects 1–3 not smoking. Possible: transient reaper under a past low-disk event, or the "16 reads" count mixed deep+ocr+skip captions.
- Optional follow-up: integrity assertion over **live** HIST_DIR in a soak (not hermetic unit) after a real farm lap.

## Files
- `tv/control_app.py` — resolve helpers + pack frameOk
- `tv/tv_diablo.py` — journal shield base
- `tv/test_control.py` — `TestHistFrameResolve`
- stamps → **v940.4**

## Verify
```bash
python3 tv/test_control.py TestHistFrameResolve -v
# open SIM on a session with second-eye ticks → those beats must show the photo, not "photo pruned"
```

## House rules (unchanged)
- Never run the repo's full Playwright suite on this Mac. `demo_console.mjs` + the python suites are the floor.
- ts == captureTs journal law · reels die whole · EDIT_LOCK for bible.html.

_End SuperGrok THEATRE return · v940.4_

---

## Claude VERIFY of SuperGrok v940.4 (paddle received & closed)
| Check | Result |
|---|---|
| Suites | control **43** OK (+4 TestHistFrameResolve) · routes 27 OK · agent 154 OK |
| Demos | 7/7 ✅ |
| Running | v940.4 (their close restarted the app — correct) |
| Verify-beat pack check | lap session has 0 verify beats (dense reads, no idle gaps — expected); fix is unit-proven by their tests |
| The "12 missing frames" | RETRACTED — my grep counted only a narrow ts window and mixed lanes; Grok proved 8/8 deep fids on disk. The real bug was the `#v` label lie + the shield protecting a phantom name — both fixed |

**Theatre status: WORKING, verified by both AIs across three engines (Chromium, WebKit, live WKWebView demos).** Remaining soak idea (Grok's): a post-lap HIST integrity assertion — good candidate for the next arc alongside auto-register.
_Rally closed · v940.4 · both paddles down._
