#!/usr/bin/env python3
"""SYNTHETIC REELS for the vault scenarios — so the suite never depends on deletable footage again.

⚠ WHY THIS EXISTS, and it is a cost I caused. On 2026-08-28 the prune was armed to act above the
disk floor (his ruling, twice stated). Within the hour it deleted:

    reel_s_1786998671206_32230   80.5 MB   71 pages
    reel_s_1786998775577_33262   42.4 MB   35 pages

Both were SCENARIO fixtures named in vault_simulate.py. The retention planner HAS a rule for exactly
this — "the TEST SUITE opens this reel by name" — and it did not fire, because
frame_authority.test_referenced_reels globbed only tv/test_*.py and friends, and vault_simulate.py
is the module that DEFINES what the tests run. Nine cases went to a permanent skip.

v2229 widened the scan (28 -> 35 fixtures, and SIX of the seven newly protected were already gone —
four deleted before that day). That stops the bleeding. It does not fix the underlying arrangement,
which is that a suite proving how the VAULT DECIDES was holding gigabytes of his disk hostage to do
it, and a single deletion could silence it.

THE RULE THIS RESTORES: fixtures must not touch live data. It has always been written the other way
round — a fixture must not reach into his real ledgers — and this is the same rule from the other
side: LIVE DATA MANAGEMENT must not be able to eat the fixtures.
[[feedback-fixtures-never-touch-live-data]] [[feedback-blind-fixture-green-gate]]

WHAT A SCENARIO ACTUALLY NEEDS, measured rather than assumed:
  * vault_simulate._reel_frames reads chronicle_retro.load_index(reel_dir) and wants
    {"frames": [{"f": <basename>}, ...]} — names and order, nothing else.
  * the READER is scripted, so no pixel is ever interpreted.
  * BUT vault_simulate.run passes sig=chronicle_retro.jpeg_sig, which DOES read the bytes to
    fingerprint each frame. The sweep dedupes on that signature, so every frame needs DISTINCT
    pixels or two frames collapse into one and a scenario silently loses a witness.

So: real files, tiny, deterministic, and provably distinct. About 30 KB for a whole tree instead of
123 MB of his footage.
"""

import io
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# The three reels the scenarios name. Kept as SYNTHETIC ids with a stamp no recording can carry
# (1500000000000 is 2017, before the project existed) — the trap frame_authority's own docstring
# records: v2071 wrote a plausible-looking reel id into a guard as an illustration, the orphan fold
# minted that exact directory, and retention began holding 3.15 GB of real footage with a reason
# that was false. A name that cannot collide with a recording cannot repeat that.
# ⚠ SIZED FROM THE SCENARIOS, NOT GUESSED. My first cut built THREE reels and
# `junk-at-the-throw-bar` needs FOUR — the whole point of that scenario is that a junk flag may only
# be SUGGESTED for discard after four separate recordings. With three it landed in `owned` instead
# of `throwOut`, so the fixture quietly tested a weaker rule than the one under assertion. A fixture
# one short of the bar it exists to prove is the blind-fixture defect in its purest form.
# Measured across the 6 scenarios: max reels 4, max frames 12. Five reels leaves headroom.
REELS = ("reel_s_1500000000001_1", "reel_s_1500000000002_1", "reel_s_1500000000003_1",
         "reel_s_1500000000004_1", "reel_s_1500000000005_1")
FRAMES_PER_REEL = 24


def _tiny_jpeg(seed):
    """A small JPEG whose bytes are unique to `seed`. -> bytes or None if PIL is absent."""
    try:
        from PIL import Image
    except Exception:
        return None
    # 32x32 is plenty for a signature and costs ~700 bytes. The pixel block is derived from the
    # seed so no two frames can share a fingerprint.
    im = Image.new("RGB", (32, 32), (seed % 251, (seed * 7) % 241, (seed * 13) % 239))
    for x in range(0, 32, 4):
        for y in range(0, 32, 4):
            v = (seed * (x + 1) * (y + 1)) % 255
            im.putpixel((x, y), (v, (v * 3) % 255, (v * 5) % 255))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88)
    return b.getvalue()


def materialise(root, reels=REELS, frames=FRAMES_PER_REEL):
    """Build a throwaway hist tree. -> (hist_path, why_not)

    Returns (None, reason) rather than half a tree when it cannot build one — a scenario running
    against a partial fixture is the blind-fixture defect wearing a new hat.
    """
    probe = _tiny_jpeg(1)
    if probe is None:
        return None, "PIL is not available, so no frame bytes can be written"
    hist = os.path.join(root, "frames", "hist")
    try:
        os.makedirs(hist, exist_ok=True)
        seed = 0
        for reel in reels:
            d = os.path.join(hist, reel)
            os.makedirs(d, exist_ok=True)
            rows = []
            for i in range(frames):
                seed += 1
                name = "%s_%04d.jpg" % (reel, i)
                with open(os.path.join(d, name), "wb") as fh:
                    fh.write(_tiny_jpeg(seed))
                # `ts` ascending so any ordering the sweep applies is stable and reproducible
                rows.append({"f": name, "ts": 1500000000000 + seed * 1000})
            with io.open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"reel": reel, "frames": rows,
                           "focus": "stash",     # an OWNERSHIP surface, or the vault lane skips it
                           "synthetic": True}, fh)
    except Exception as e:
        return None, "could not build the fixture tree: %s" % str(e)[:110]
    return hist, None


def signatures_are_distinct(hist, reels=REELS):
    """Prove every frame fingerprints differently. -> (ok, why)

    ⚠ THIS IS THE ONE PROPERTY THE WHOLE FIXTURE RESTS ON. vault_retro dedupes by signature, so two
    identical frames are ONE witness — a scenario asserting "three recordings ground it" would fail
    for a reason that has nothing to do with the rule under test. Solid-colour placeholders would
    look perfectly reasonable and be silently wrong.
    """
    try:
        import chronicle_retro as cr
    except Exception as e:
        return False, "chronicle_retro did not import: %s" % str(e)[:80]
    seen, n = {}, 0
    for reel in reels:
        d = os.path.join(hist, reel)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".jpg"):
                continue
            n += 1
            try:
                s = cr.jpeg_sig(os.path.join(d, f))
            except Exception as e:
                return False, "jpeg_sig refused %s: %s" % (f, str(e)[:60])
            if s in seen:
                return False, ("%s and %s share a signature — the sweep would count them as one "
                               "witness" % (seen[s], f))
            seen[s] = f
    if not n:
        return False, "no frames were written"
    return True, None


def cleanup(root):
    """Remove a tree built by materialise(). Never raises."""
    try:
        shutil.rmtree(os.path.join(root, "frames"), ignore_errors=True)
    except Exception:
        pass


def main(argv=None):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    import tempfile
    root = tempfile.mkdtemp(prefix="vault-fixture-")
    try:
        hist, why = materialise(root)
        if not hist:
            print("⚪ UNKNOWN — %s" % why)
            return 2
        ok, why = signatures_are_distinct(hist)
        total = sum(os.path.getsize(os.path.join(dp, f))
                    for dp, _, fs in os.walk(hist) for f in fs)
        print("built %d reel(s) x %d frames in %s" % (len(REELS), FRAMES_PER_REEL, hist))
        print("  total size: %.1f KB   (his real fixtures were 123 MB)" % (total / 1024.0))
        print("  %s" % ("🟢 every frame fingerprints distinctly"
                        if ok else "🔴 %s" % why))
        return 0 if ok else 1
    finally:
        cleanup(root)
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
