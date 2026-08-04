#!/usr/bin/env python3
"""v1636 — guard the ten boss portraits against being silently swapped again.

WHAT THIS DOES AND, MORE IMPORTANTLY, WHAT IT DOES NOT DO.

It compares the bytes on disk against art/boss_portraits.manifest.json, which records the sha256 of
each portrait AS A HUMAN LAST OPENED IT, next to a sentence saying what that human saw. That is the
whole trick. The hash proves nothing about content; it proves only "these are still the bytes
somebody looked at". A CHANGED verdict is therefore not a failure — it is a request for a person to
open the image and either bless the new pixels or restore the old ones.

Why the bar is that low: art/mephisto_graphic.png shipped as a blue soulstone gem and
art/diablo_graphic.png as a leather-bound book from v269 (2026-06-14) to v1636 (2026-08-04), and
EVERY automated check passed for seven weeks. The path resolved. naturalWidth was > 0. An md5 sweep
of art/ found zero duplicates. File size flagged Mephisto at 10KB and sailed straight past Diablo at
46KB, which was a book. v1629 then "fixed" the bug by confirming the filename in the map. A file
that loads is not a file that is right, and no checker that never opens an image can tell you which
you have — so this one does not pretend to.

The cause was a fuzzy base-item matcher in v269 that rewrote 230 art/*_graphic.png files from item
art and had no idea that two of its slugs, 'mephisto' and 'diablo', name BOSSES as well as items
(Mephisto's Soulstone; a tome). Those two filenames are permanently ambiguous. Anything that bulk-
writes art/ by name must skip them, and this script is how the next bulk write gets caught.

    python3 art/verify_boss_portraits.py          # exit 0 all match, 1 something changed/missing
    python3 art/verify_boss_portraits.py --list   # print the human descriptions, check nothing

To re-bless a portrait: OPEN IT, decide in words what it depicts, then update 'depicts', 'bytes' and
'sha256' for that row in the manifest. Editing the hash without opening the image reintroduces
exactly the bug this file exists to prevent.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "boss_portraits.manifest.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    with open(MANIFEST, encoding="utf-8") as fh:
        rows = json.load(fh)["portraits"]

    if "--list" in argv:
        for r in rows:
            print("%-10s %-28s %s" % (r["bossId"], r["file"], r["depicts"]))
        return 0

    bad = []
    for r in rows:
        path = os.path.join(HERE, r["file"])
        if not os.path.exists(path):
            bad.append((r, "MISSING", "no file at art/%s — ten thumbnails would 404" % r["file"]))
            continue
        got = sha256(path)
        if got != r["sha256"]:
            bad.append((r, "CHANGED", "sha256 %s..., manifest says %s..." % (got[:12], r["sha256"][:12])))

    for r, kind, detail in bad:
        print("%-8s %-10s %s" % (kind, r["bossId"], detail))
        print("         last human-verified content: %s" % r["depicts"])
    if bad:
        print("\n%d of %d portraits no longer match what a human verified." % (len(bad), len(rows)))
        print("OPEN each one and look at it. Do not re-bless a hash you have not seen the picture for.")
        return 1
    print("all %d boss portraits match the human-verified manifest" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
