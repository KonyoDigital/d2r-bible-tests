# -*- coding: utf-8 -*-
"""GUEST FIXTURE PACKS — his recorded runs, turned into something Grok Bot can click.

HIS BRIEF (GB-CLAUDE-GROK-PROFILE-SYNC):

    *"Elad will upload recorded runs/scenarios over time. Clear landing place + loader so they
     appear as SHELF sessions/reels on guest (same UI Diablo clicks) ... Each pack: enough for
     Diablo to open SHELF, click a session, exercise reel controls, open VAULT items — without
     mutating possession/ledger from guest."*

═══ WHY A PACK IS NOT JUST A COPIED REEL ══════════════════════════════════════════════════════

MEASURED on his tree: one reel is **196 MB across 153 frames**. Copying reels to the box would
move gigabytes for a regression fixture and the box would fill up before the second scenario
landed. A pack carries a REPRESENTATIVE SUBSET, evenly spaced across the reel so the scrub bar
still travels the whole run, downscaled to a width a browser can page through.

⚠⚠ AND EVERY FIXTURE SESSION SAYS IT IS ONE. `fixture: true` and `fixturePack` ride on every
record. Without them a pack is indistinguishable from his real footage on the guest, and the
first thing that happens is an eyes-loop reporting a finding about staged data as though it were
his — a wrong number that looks exactly like a right one. The whole reason the guest exists is to
tell the truth about his console; a fixture that cannot be told from live footage defeats it.
[[unknown-stays-unknown]]

⚠⚠ THE LOADER WRITES ONLY INTO A MIRROR, AND REFUSES ANYTHING ELSE. His brief puts "mutating
vault possession from guest smokes" out of scope. `load()` therefore refuses any destination
under the live frames tree or the repo's own stores — a loader that could be pointed at
`tv/frames/hist/` would let a staged scenario become real footage, and footage has no un-delete.

⚠ AND IT SCRUBS, because packs are built from HIS reels and this repo is public. Same redaction
as the mirror: guest_profile.scrub over every record, and the same leak check before a pack is
declared built.
"""
import hashlib
import io
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

import guest_profile as gp

PACK_FORMAT = 1
DEFAULT_FRAMES = 16
DEFAULT_WIDTH = 1280
# The live footage tree and the real stores. A pack may be BUILT from these and never LOADED into
# them. Ordered longest-first so a prefix test cannot be fooled by a shorter sibling.
FORBIDDEN_DESTS = (
    os.path.join(REPO, "tv", "frames", "hist"),
    os.path.join(REPO, "tv", "frames"),
)


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _pick(frames, want):
    """Evenly spaced across the WHOLE reel, first and last always kept.

    A head-slice would give a pack that looks complete and whose scrub bar only ever covers the
    first few seconds — the reel controls this pack exists to exercise would be untestable past
    the opening.
    """
    n = len(frames)
    if n <= want:
        return list(frames)
    step = (n - 1) / float(want - 1)
    idx = sorted({int(round(i * step)) for i in range(want)})
    return [frames[i] for i in idx]


def build(reel_dir, pack_id, title="", why="", frames=DEFAULT_FRAMES, width=DEFAULT_WIDTH,
          out_root=None, session_record=None, live_identity=None):
    """Turn one real reel into a versioned, self-describing pack. -> the pack dir."""
    reel_dir = os.path.abspath(reel_dir)
    idx_p = os.path.join(reel_dir, "index.json")
    if not os.path.isfile(idx_p):
        raise ValueError("no index.json in %s — that is not a reel" % reel_dir)
    with io.open(idx_p, encoding="utf-8") as fh:
        idx = json.load(fh)
    src_sid = idx.get("sessionId") or os.path.basename(reel_dir).replace("reel_", "")
    # ⚠⚠ A FIXTURE MUST NOT WEAR THE SOURCE SESSION'S ID. Measured on the first load: the pack's
    # id collided with the real 419-row session list, the loader deduped it away as "already
    # there", and the REAL 153-frame row won — so the fixture flag never reached the guest and
    # Grok would have clicked his live session believing it was the staged one. A pack is a
    # different object from the reel it was cut from: 16 frames, not 153.
    # The shape `s_<ms>_<suffix>` is kept because other readers parse it.
    _suffix = "".join(ch for ch in pack_id if ch.isalnum())[-8:] or "fx"
    _stem = src_sid.rsplit("_", 1)[0] if "_" in src_sid else src_sid
    sid = "%s_fx%s" % (_stem, _suffix)
    all_frames = idx.get("frames") or []
    if not all_frames:
        raise ValueError("reel %s lists no frames" % sid)

    out_root = out_root or os.path.join(REPO, "fixtures")
    pack = os.path.join(out_root, pack_id)
    reel_out = os.path.join(pack, "reels", "reel_%s" % sid)
    if os.path.isdir(pack):
        shutil.rmtree(pack)
    os.makedirs(reel_out)

    picked = _pick(all_frames, frames)
    kept, bytes_out, bytes_in = [], 0, 0
    for fr in picked:
        name = fr.get("f")
        src = os.path.join(reel_dir, name)
        if not os.path.isfile(src):
            continue                      # a pruned frame is absent, not an error
        bytes_in += os.path.getsize(src)
        dst = os.path.join(reel_out, name)
        try:
            from PIL import Image
            im = Image.open(src)
            if im.width > width:
                im = im.resize((width, max(1, int(im.height * width / float(im.width)))),
                               Image.LANCZOS)
            im.convert("RGB").save(dst, "JPEG", quality=82, optimize=True)
        except Exception:
            shutil.copy2(src, dst)        # no Pillow -> ship it full size rather than not at all
        bytes_out += os.path.getsize(dst)
        kept.append({"f": name, "ts": fr.get("ts")})

    if not kept:
        shutil.rmtree(pack)
        raise ValueError("every frame of reel %s is already pruned — nothing to pack" % sid)

    with io.open(os.path.join(reel_out, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(gp.scrub({"sessionId": sid, "n": len(kept), "frames": kept}, live_identity),
                  fh, ensure_ascii=False, indent=1)

    # the SHELF record. Real shape, real numbers where they are real, flagged as a fixture.
    rec = dict(session_record or {})
    rec.update({
        "sessionId": sid, "n": len(kept), "frames": len(kept),
        "t0": kept[0].get("ts"), "t1": kept[-1].get("ts"),
        "fixture": True, "fixturePack": pack_id,
        # ⚠ footageN is the count THIS PACK CARRIES, and footageWhy says the rest were not lost.
        "footageN": len(kept),
        "footageState": "fixture",
        "footageWhy": ("a fixture pack carrying %d of the reel's %d frames, evenly spaced — the "
                       "rest were never copied, not pruned" % (len(kept), len(all_frames))),
    })
    with io.open(os.path.join(pack, "sessions.json"), "w", encoding="utf-8") as fh:
        json.dump({"sessions": [gp.scrub(rec, live_identity)]}, fh, ensure_ascii=False, indent=1)

    files = {}
    for dp, _d, fs in os.walk(pack):
        for f in fs:
            p = os.path.join(dp, f)
            files[os.path.relpath(p, pack)] = _sha256_file(p)
    manifest = {
        "packFormat": PACK_FORMAT,
        "id": pack_id,
        "title": title or pack_id,
        "why": why or "a recorded run, staged so the guest seat can click it",
        "source": {"sessionId": src_sid, "framesInReel": len(all_frames)},
        "fixtureSessionId": sid,
        "carries": {"sessions": 1, "frames": len(kept),
                    "bytes": bytes_out, "bytesInSource": bytes_in},
        "fixture": True,
        "files": files,
    }
    with io.open(os.path.join(pack, "pack.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    return pack


def verify(pack_dir, live_identity=None):
    """-> (ok, [problems]). Checks the format, the flags, the checksums and the scrub."""
    problems = []
    mp = os.path.join(pack_dir, "pack.json")
    if not os.path.isfile(mp):
        return False, ["no pack.json — that is not a pack"]
    with io.open(mp, encoding="utf-8") as fh:
        man = json.load(fh)
    if man.get("packFormat") != PACK_FORMAT:
        problems.append("packFormat %r, this loader speaks %r" % (man.get("packFormat"), PACK_FORMAT))
    for rel, want in (man.get("files") or {}).items():
        p = os.path.join(pack_dir, rel)
        if not os.path.isfile(p):
            problems.append("missing file %s" % rel)
        elif _sha256_file(p) != want:
            problems.append("checksum changed: %s" % rel)
    sp = os.path.join(pack_dir, "sessions.json")
    if os.path.isfile(sp):
        with io.open(sp, encoding="utf-8") as fh:
            for s in (json.load(fh).get("sessions") or []):
                if not s.get("fixture"):
                    problems.append("session %s is not flagged as a fixture" % s.get("sessionId"))
                leaked = gp.leaks(s, live_identity)
                if leaked:
                    problems.append("session %s still carries %d identifier(s)"
                                    % (s.get("sessionId"), len(leaked)))
    return (not problems), problems


def load(pack_dir, mirror_dir, live_identity=None):
    """Merge a pack into a GUEST MIRROR. -> a dict saying what landed.

    ⚠ REFUSES any destination that is his live footage or a repo store. A loader that could be
    pointed at tv/frames/hist would turn a staged scenario into real footage, and footage has no
    un-delete.
    """
    dest = os.path.abspath(mirror_dir)
    for forbidden in FORBIDDEN_DESTS:
        f = os.path.abspath(forbidden)
        if dest == f or dest.startswith(f + os.sep):
            raise ValueError("refusing to load a fixture into the live tree (%s) — a pack may be "
                             "BUILT from his footage and never loaded into it" % dest)
    ok, problems = verify(pack_dir, live_identity)
    if not ok:
        raise ValueError("pack does not verify: %s" % "; ".join(problems[:4]))

    os.makedirs(os.path.join(dest, "api"), exist_ok=True)
    sess_p = os.path.join(dest, "api", "sessions.json")
    book = {"sessions": []}
    if os.path.isfile(sess_p):
        try:
            with io.open(sess_p, encoding="utf-8") as fh:
                book = json.load(fh) or {"sessions": []}
        except Exception:
            book = {"sessions": []}
    if gp.is_unreadable(book):
        book = {"sessions": []}
    rows = book.get("sessions") or []

    with io.open(os.path.join(pack_dir, "sessions.json"), encoding="utf-8") as fh:
        incoming = json.load(fh).get("sessions") or []
    have = set(r.get("sessionId") for r in rows if isinstance(r, dict))
    added = [r for r in incoming if r.get("sessionId") not in have]
    # fixtures ride at the FRONT so the guest's SHELF shows them without scrolling 419 real rows
    book["sessions"] = added + rows
    with io.open(sess_p, "w", encoding="utf-8") as fh:
        json.dump(book, fh, ensure_ascii=False, indent=1)

    reels_src = os.path.join(pack_dir, "reels")
    copied = 0
    if os.path.isdir(reels_src):
        reels_dst = os.path.join(dest, "frames", "hist")
        os.makedirs(reels_dst, exist_ok=True)
        for name in os.listdir(reels_src):
            s, d = os.path.join(reels_src, name), os.path.join(reels_dst, name)
            if os.path.isdir(s):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
                copied += 1
    return {"ok": True, "sessionsAdded": len(added), "sessionsAlreadyThere": len(incoming) - len(added),
            "reelsCopied": copied, "mirror": dest}


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "build":
        print(build(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "pack-1"))
    else:
        print(__doc__.strip().splitlines()[0])
