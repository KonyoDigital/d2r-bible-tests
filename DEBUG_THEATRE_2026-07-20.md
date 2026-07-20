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

## House rules (unchanged)
- Never run the repo's full Playwright suite on this Mac. `demo_console.mjs` + the python suites are the floor.
- ts == captureTs journal law · reels die whole · EDIT_LOCK for bible.html.
