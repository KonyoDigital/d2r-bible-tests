#!/usr/bin/env python3
# 📺 TV DIABLO — end-to-end SIMULATOR (no game, no vision cost).
#
# Plays a scripted "farming session" through the REAL bridge: starts the same
# localhost server the live agent uses, then publishes reads on a timer —
# a rune drop, a unique, a set piece, junk, a repeat. Point the bible's 📺
# panel at it (flip the switch) and every stage of the receiver can be
# debugged: connect animation, feed, routing (🪨/🏆/🧩/📋), apply, offline.
#
#   python3 tv/simulate.py           # ~2 reads/8s, loops the script, Ctrl-C to stop
#   python3 tv/simulate.py --fast    # one read per 2s (headless test cadence)
#
# The vision layer itself is validated separately:
#   python3 tv/tv_diablo.py --test <screenshot.png>   (run in YOUR terminal —
#   it is one plain `claude -p` call on your subscription)
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tv_diablo

SCRIPT = [
    ["Ist Rune"],                                          # 🪨 rune pickup
    ["Skin of the Vipermagi", "Perfect Ruby"],             # 🏆 unique + note
    ["Sigon's Guard", "Vex Rune"],                         # 🧩 set piece + 🪨 rune
    [],                                                    # gameplay frame — nothing readable
    ["Harlequin Crest", "Tal Rasha's Horadric Crest"],     # 🏆 + 🧩
    ["Superior Mage Plate of the Whale"],                  # 📋 unroutable note
]

def main():
    fast = "--fast" in sys.argv
    with tv_diablo._state_lock:
        tv_diablo._save({"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0, "sim": True})
    tv_diablo.bridge()
    print(f"📺 TV DIABLO SIMULATOR — bridge live on http://127.0.0.1:{tv_diablo.PORT}/state")
    print("   open the bible → ⚡ session → 📺 TV DIABLO → flip the switch. Ctrl-C stops (= agent-offline state).\n")
    n = 0
    while True:
        for names in SCRIPT:
            time.sleep(2 if fast else 8)
            n += 1
            with tv_diablo._state_lock:
                st = tv_diablo._load()
                st["reads"].append({"ts": int(time.time()*1000), "names": names})
                st["reads"] = st["reads"][-200:]
                st["readCount"] = n
                tv_diablo._save(st)
            print(f"  ▶ read #{n}: {' · '.join(names) if names else '(gameplay frame)'}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n📺 sim off.")
