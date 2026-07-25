# G5 Grok Eyes — check list (Konyo style)

Restore point (before this work):  
`~/RESTORE_POINTS/d2r_bible_tests_v1379.3_2026-07-25_022539/`

## Gates already green (automated)
```bash
cd /Users/konyo/d2r_bible_tests
python3 tv/test_g5_grok_eyes.py -v          # OFF path inert
python3 -m py_compile tv/g5_grok_eyes.py tv/tv_diablo.py tv/control_app.py
TV_STUB=1 python3 -c "import sys;sys.path.insert(0,'tv');import tv_diablo as t; assert t.claude_read('x')['mode']=='stub'"
```

## Phase 1 — Sidecar (isolated prove)
1. `export XAI_API_KEY=...`
2. `python3 tv/g5_sidecar/server.py`
3. `curl -s http://127.0.0.1:8765/health | python3 -m json.tool` → `ready: true` if key set
4. POST a real hist frame path → JSON with `names`/`scene`
5. Kill sidecar. Main TV-D never knew it existed.

## Phase 2 — Shadow (parallel, Claude still drives)
1. Control app running; key set
2. `curl -s -X POST http://127.0.0.1:PORT/api/g5_toggle -H 'content-type: application/json' -d '{"mode":"shadow"}'`
3. `curl -s http://127.0.0.1:PORT/api/g5_status` → mode shadow, on true
4. Run ON AIR / one agent read as usual (Claude)
5. Check `tv/g5_shadow.jsonl` grows with claude_names vs grok_names
6. Flip off: `{"mode":"off"}` — shadow stops; Claude unchanged

## Phase 3 — Primary (only after 1+2 OK)
1. Same toggle `{"mode":"primary"}`
2. One test read / short ON AIR — expect `mode` like `g5-primary` on results
3. Pull key or mode off → falls back to Claude
4. Doctor: with primary+key, claude_cli/auth soften to warn (not block)

## Abort / restore
- Always `mode: off` or delete `tv/g5_grok_eyes.state`
- Full tree restore: see RESTORE_POINTS HOW_TO_RESTORE.md
- Rip feature: G5_GROK_EYES_REMOVAL.md
