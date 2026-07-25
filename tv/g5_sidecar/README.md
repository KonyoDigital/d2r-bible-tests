# G5 Sidecar — SuperGrok subscription prove

Uses **`grok -p`** + your SuperGrok login.  
**Does not** use `XAI_API_KEY` or console API tokens.

## Setup once
```bash
grok login    # SuperGrok / Grok Build OIDC
```

## Run
```bash
cd /Users/konyo/d2r_bible_tests
# do NOT export XAI_API_KEY
python3 tv/g5_sidecar/server.py
```

## Prove
```bash
curl -s http://127.0.0.1:8765/health | python3 -m json.tool
# ready:true when logged in

curl -s -X POST http://127.0.0.1:8765/read \
  -H 'content-type: application/json' \
  -d "{\"path\":\"/ABS/PATH/TO/frame.jpg\"}" | python3 -m json.tool
```

Main app G5 can stay **OFF** — sidecar uses `force=True` but still **subscription CLI only**.
